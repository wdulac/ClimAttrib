from dash import html, callback, Output, Input, State
from dash import clientside_callback, ClientsideFunction
from dash import dcc
from dash.exceptions import PreventUpdate
from dash_extensions.javascript import Namespace
import dash_leaflet as dl
import json

ZOOM_LEVEL_THRESHOLD = 4
DEFAULT_ZOOM_LEVEL = 3
MINIMUM_ZOOM_LEVEL = 3
MAP_CENTER_POSITION = [40, 0]
MAP_MAX_BOUNDS = [[-70, -180], [83, -180], [83, 180], [-70, 180]]

# Load JS namespace from assets/js/leaflet_extras.js
ns = Namespace('dashExtensions', 'geojson')

_grid = dl.GeoJSON(
    url='/assets/static/grid.geojson',
    style=ns('colorCell'),
    hoverStyle=dict(
        fillOpacity=0.3
    ),
    hideout={'selected': None},
    id='geojson'
)

location_selector = html.Div(
    children=[
        dl.Map(
            children=[
                dl.FullScreenControl(),
                dl.TileLayer(noWrap=True),
                dl.LayerGroup(id='marker'),
                dl.LayerGroup(id='grid'),
                html.Div(id='zoom-to-select', children="Zoom-in to select a grid cell")
            ],
            center=MAP_CENTER_POSITION,
            zoom=DEFAULT_ZOOM_LEVEL,
            minZoom=MINIMUM_ZOOM_LEVEL,
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


# TODO Try to make the grid faster (Client-side callback with custom JS ?)
@callback(
    Output('grid', 'children'),
    Input('map', 'zoom'),
    State('grid', 'children'),
)
def show_grid(current_zoom_level, grid_state):
    """
    Show the geojson grid passed a certain zoom level.
    """

    if grid_state is not None:
        if current_zoom_level >= ZOOM_LEVEL_THRESHOLD:
            # Zooming further down with the grid already displayed. No need to update.
            raise PreventUpdate
        else:
            # Zooming out below the threshold with the grid displayed; we remove the grid
            return None
    elif current_zoom_level >= ZOOM_LEVEL_THRESHOLD:
        # The grid is not displayed and we pass the zoom threshold
        return _grid
    else:
        # The grid is not displayed but we are not at the threshold; no need to update
        raise PreventUpdate

    
clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='select_point'),
    Output('geojson', 'hideout'),
    Output('input:selected-point', 'data'),
    Input('geojson', 'clickData')
)


@callback(
    Output('marker', 'children', allow_duplicate=True),
    Output('input:selected-point', 'data', allow_duplicate=True),
    Input('map', 'zoom'),
    State('marker', 'children'),
    prevent_initial_call=True
)
def clear_point_data(zoom_level, marker_state):
    """
    Clear out both the marker and the stored value when zooming out
    passed the the globally set zoom level threshold.
    """

    if zoom_level < ZOOM_LEVEL_THRESHOLD:
        if marker_state is not None:
            return None, None
        else:
            raise PreventUpdate
    else:
        raise PreventUpdate