"""
Interactive location selector — Leaflet map on the home page.

Renders a world map (``dl.Map``) with a GeoJSON overlay of model grid cells. The user
zooms in, clicks a cell to select a location, and the coordinates are stored in a
``dcc.Store`` for other components to consume.

## Layout

- ``dl.Map`` (id: ``map``) — Leaflet map with a fullscreen control, a base tile layer,
  and a ``LayerGroup`` for a selection marker.
- ``dl.GeoJSON`` (id: ``geojson``) — receives grid cell features fetched tile by tile
  from ``/api/grid_tiles`` as the user pans and zooms. Uses client-side JS functions
  to style the selected cell (``colorCell``) and hide all cells below the zoom
  threshold (``zoomFilter``). Both functions are in ``assets/js/leaflet_extras.js``.
- ``#zoom-to-select`` — a text hint shown when zoom level is below
  ``ZOOM_LEVEL_THRESHOLD`` (4).
- ``dcc.Store(id='input:selected-point')`` — canonical source of truth for the
  selected ``[lat, lon]`` pair; consumed by ``input_settings_top_bar`` callbacks.
- ``#home-plots-panel`` — a panel toggled by ``toggle_plots`` (in this module) that
  displays the annual cycle and Yo timeseries once a valid selection is made.

## Callbacks

Server-side:

- ``zoom_to_select`` — shows/hides the zoom hint based on current zoom level.
- ``clear_point_data`` — clears ``geojson.clickData`` when the user zooms out, to
  prevent the previous selection from being re-applied on the next zoom-in.
- ``toggle_plots`` — shows the contextual plots panel once a valid point and date
  range are both set.

Client-side (in ``assets/js/leaflet_extras.js``):

- ``clientside.updateGridTiles`` — fetches tile features from ``/api/grid_tiles`` for
  the current map bounds.
- ``clientside.select_point`` — updates the GeoJSON ``hideout`` (which drives cell
  highlighting) and writes the selected coordinates to ``input:selected-point``.
- ``clientside.update_zoom`` — keeps ``hideout.zoom`` in sync with the map zoom level,
  needed by the ``zoomFilter`` JS function.

## Key component IDs

``map``, ``geojson``, ``marker``, ``zoom-to-select``, ``input:selected-point``,
``home-plots-panel``.
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

import datetime as dt
from science.visualisation import plot_observed_Yo, plot_annual_cycle

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

interactive_map_component = html.Div(
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

    if point and not date_error:
        if None not in selected_dates:

            # Compose dict

            # Convert dates to datetime objects
            start_date_dt = dt.datetime.strptime(str(selected_dates[0]), '%Y-%m-%d')
            stop_date_dt  = dt.datetime.strptime(str(selected_dates[1]), '%Y-%m-%d')
            
            # Compute duration and middle date
            duration = (stop_date_dt - start_date_dt).days + 1

            # Coordinates
            coords = json.loads(point)
            lat, lon = coords[0], coords[1]
            
            params = {
                'extreme_type': extreme_type,
                'method': computation_method,
                'start_date': start_date_dt,
                'stop_date': stop_date_dt,
                'duration': duration,
                'lat': lat,
                'lon': lon,
                'intensity': json.loads(intensity)
            }

            panel_content = dmc.Box(
                dmc.Center(
                    dmc.Stack([
                        dcc.Graph(figure=plot_annual_cycle(params, scale=0.75)),
                        dcc.Graph(figure=plot_observed_Yo(params, scale=0.75)),
                    ], gap=0),
                ), 
            )

            return "home-plots-panel plots-visible", panel_content
        else:
            raise PreventUpdate
    return "home-plots-panel", None


# @callback(
#     Output("map", "viewport"),
#     # Input("input:selected-point", "data"),
#     Input("home-plots-panel", "className"),
#     State("input:selected-point", "data"),
#     prevent_initial_call=True
# )
# def recenter_map(panel_class, selected_point):

#     print(ctx.triggered_id)

#     # On recentre UNIQUEMENT quand le panneau s’ouvre
#     if ctx.triggered_id != "home-plots-panel":
#         raise PreventUpdate

#     if panel_class != "plots-visible":
#         raise PreventUpdate


#     lat, lon = json.loads(selected_point)

#     return dict(
#         center=[lat, lon],
#         transition="flyTo",
#     )