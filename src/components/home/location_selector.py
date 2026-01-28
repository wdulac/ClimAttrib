"""
# Module overview

This module provides the Leaflet-based location selector used on the home page.
It exposes a small Dash fragment containing an interactive map that renders a
vector grid (GeoJSON) of model grid cells, allows the user to zoom and select a
cell, and stores the selected coordinates in a dcc.Store for other UI
components to consume.

Primary features
- dl.Map configured with canvas renderer and custom max bounds / zoom limits.
- A GeoJSON layer (`geojson`) that receives tiled vector data (via a clientside
  fetch) and supports:
    - dynamic styling to highlight the selected cell,
    - client-side filtering to hide cells at low zoom levels,
    - click handling to pick a grid cell.
- A Store component (`input:selected-point`) that holds the JSON-serialized
  [lat, lon] coordinates of the currently selected grid cell.
- Small UI hint text (`zoom-to-select`) that is shown/hidden depending on zoom.

Integration & assets
- Client-side JS lives under assets/ and must provide the following functions:
  - clientside.updateGridTiles(bounds, hideout) -> fetch and return GeoJSON tiles
  - clientside.select_point(clickData, zoom, hideout) -> updated hideout + point
  - clientside.update_zoom(zoom, hideout) -> updated hideout with zoom level
  - A dashExtensions Namespace 'dashExtensions.geojson' must expose
    `colorCell` and `zoomFilter` used by the GeoJSON component.
- The helper JS `assets/js/leaflet_extras.js` is expected to contain the above
  helpers and must be present for full UX.

Callbacks (server-side)
- zoom_to_select(zoom, is_hidden):
    Toggle visibility of the "zoom to select" hint based on zoom level.
- clear_point_data(zoom, clickData):
    Clears previous clickData when zooming out to avoid reselecting cells.
- Several clientside callbacks wire the map bounds/zoom/clicks to GeoJSON data
  and to the stored selected point.

Component ids (important)
- 'map' (dl.Map)
- 'geojson' (dl.GeoJSON)
- 'marker' (dl.LayerGroup)
- 'zoom-to-select' (html.Div)
- 'input:selected-point' (dcc.Store)

Notes & recommendations
- The GeoJSON tiles fetched by the client are generally lightweight but the
  tile service must be accessible from the browser. Keep heavy work off the
  Dash server (use clientside JS).
- Use the dcc.Store `input:selected-point` as canonical source of truth for
  downstream callbacks; do not rely on GeoJSON.clickData directly.
- Keep the JS helpers in assets/ under version control; changes to their API
  must be reflected in this module and any other components that use them.

Usage
- Import and include `location_selector` in the app layout. Other components
  (e.g. input_settings_top_bar) expect `input:selected-point` to exist.
"""

from dash import html, callback, Output, Input, State, ctx
from dash import clientside_callback, ClientsideFunction
from dash import dcc
from dash.exceptions import PreventUpdate
from dash_extensions.javascript import Namespace
import dash_mantine_components as dmc
import dash_leaflet as dl
import dash_leaflet.express as dlx
import json

ZOOM_LEVEL_THRESHOLD = 4
DEFAULT_ZOOM_LEVEL = 3
MINIMUM_ZOOM_LEVEL = 3
MAP_CENTER_POSITION = [40, 0]
MAP_MAX_BOUNDS = [[-70, -180], [83, -180], [83, 180], [-70, 180]]

# Load JS namespace from assets/js/leaflet_extras.js
ns = Namespace('dashExtensions', 'geojson')

_grid = dl.GeoJSON(
    data=None,
    style=ns('colorCell'), # Dynamically highlights selected cell
    hoverStyle=dict(
        fillOpacity=0.3
    ),
    filter=ns('zoomFilter'), # Responsible for making cells (dis)appear w/ zoom
    hideout={
        'selected': None,
        'zoom': DEFAULT_ZOOM_LEVEL,
        'zoom_threshold': ZOOM_LEVEL_THRESHOLD 
    },
    zoomToBounds=False,
    id='geojson'
)

location_selector = html.Div(
    children=[
        dl.Map(
            children=[
                dl.FullScreenControl(),
                dl.TileLayer(noWrap=True),
                dl.LayerGroup(id='marker'),
                _grid,
                html.Div(id='zoom-to-select', children="Zoom-in to select a grid cell")
            ],
            center=MAP_CENTER_POSITION,
            zoom=DEFAULT_ZOOM_LEVEL,
            minZoom=MINIMUM_ZOOM_LEVEL,
            renderer={
                'method': 'canvas'
            },
            maxBounds=MAP_MAX_BOUNDS,
            id='map',
            className='map-container'
        ),
        dcc.Store(id='input:selected-point', data=None),
        
    ],
    className='map-parent-container'
)
 

#~~~~~~~ Callbacks

@callback(
        Output('zoom-to-select', 'hidden'),
        Input('map', 'zoom'),
        State('zoom-to-select', 'hidden'),
        prevent_initial_call=True
)
def zoom_to_select(zoom_level, is_hidden):
    """
    Uses zoom level to determine wether or not to hide the large
    "Zoom to select a grid point" indicator on the leaflet map.
    """

    if zoom_level >= ZOOM_LEVEL_THRESHOLD:
        if is_hidden:
            raise PreventUpdate
        else:
            return True
    else:
        if is_hidden:
            return False
        else:
            raise PreventUpdate


@callback(
    Output('geojson', 'clickData'),
    Input('map', 'zoom'),
    State('geojson', 'clickData'),
    prevent_initial_call=True
)
def clear_point_data(zoom_level, clickData):
    """
    Clear out 'GeoJSON's clickData attribute based when zooming-out.
    Otherwise it reselects the previous point when zooming back-in, even if it
    had previously been cleared.
    """

    if zoom_level < ZOOM_LEVEL_THRESHOLD:
        if clickData is not None:
            return None
        else:
            raise PreventUpdate
    else:
        raise PreventUpdate


# Compose and fetch request to grid tiles that fit within map bounds
clientside_callback(
    ClientsideFunction(
        namespace='clientside',
        function_name='updateGridTiles'
    ),
    Output('geojson', 'data'),
    Input('map', 'bounds'),
    Input('geojson', 'hideout') # Trigger on hideout so that zoom level is always up to date
)


# Select point (which triggers colorCell) and store coordinates
clientside_callback(
    ClientsideFunction(
        namespace='clientside',
        function_name='select_point'
    ),
    Output('geojson', 'hideout'),
    Output('input:selected-point', 'data'),
    Input('geojson', 'clickData'),
    Input('map', 'zoom'),
    State('geojson', 'hideout'),
    prevent_initial_call=True
)


# Update geojson's hideout prop with current zoom level 
clientside_callback(
    ClientsideFunction(
        namespace='clientside',
        function_name='update_zoom'
    ),
    Output('geojson', 'hideout', allow_duplicate=True),
    Input('map', 'zoom'),
    State('geojson', 'hideout'),
    prevent_initial_call=True
)

@callback(
    Output("home-plots-panel", "className"),
    Output("home-plots-panel", "children"),
    Input("input:selected-point", "data"),
    Input("input:date", "error"),
    Input("data:intensity", "data"),
    Input("input:extreme-type", "value"),
    Input("input:computation-method", "value"),
    State("input:date", "value"),
    prevent_initial_call=True
)
def toggle_plots(
    point: str, # JSON serialized
    date_error:str,
    intensity:str, # JSON serialized
    extreme_type: str,
    computation_method: str,
    selected_dates: list[str, str]
):

    print("TOGGLE_PLOTS TRIGGERED BY : ", ctx.triggered_prop_ids)

    if point and not date_error:
        if None not in selected_dates:
            return "plots-visible", dmc.Box(
                dmc.Center(
                    dmc.Text(
                        "Contenu du panneau"
                    ),
                    style={"height": "100%"}
                ),
                style={"height": "100%"},
            )
        else:
            print("Update prevented")
            raise PreventUpdate
    return "plots-hidden", None