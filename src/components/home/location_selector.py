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
    id='geojson'
)

location_selector = html.Div(
    children=[
        dl.Map(
            children=[
                dl.FullScreenControl(),
                dl.TileLayer(noWrap=True),
                dl.LayerGroup(id='marker'),
                dl.LayerGroup(id='grid', children=[_grid]),
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


# Select point (which triggers colorCell) and store coordinates
clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='select_point'),
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
    Output('input:selected-point', 'data', allow_duplicate=True),
    Output('geojson', 'clickData'),
    Input('map', 'zoom'),
    State('input:selected-point', 'data'),
    State('geojson', 'clickData'),
    prevent_initial_call=True
)
def clear_point_data(zoom_level, data, clickData):
    """
    Clear out both the marker and the stored value when zooming out
    passed the the globally set zoom level threshold.
    """

    if zoom_level < ZOOM_LEVEL_THRESHOLD:
        if clickData is not None:
            return None, None
        else:
            raise PreventUpdate
    else:
        raise PreventUpdate