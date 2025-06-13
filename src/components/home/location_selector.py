from dash import html, callback, Output, Input, State
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


_custom_icon=dict(
    iconUrl='/assets/static/marker-icon.png',
    # shadowUrl='https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
    iconSize=[25,40]
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

    
@callback(
    Output('marker', 'children'),
    Output('input:selected-point', 'data'),
    Input('geojson', 'clickData')
)
def select_point(click_data):
    """
    Place a marker on the selected geojson grid point and return its coordinates
    (the center) to the Store unit (i.e the browser's memory)
    """

    def center_from_polygon(coordinates):
        lon_min, lon_max = coordinates[0][0], coordinates[2][0]
        lat_min, lat_max = coordinates[0][1], coordinates[1][1]
        return [lat_min + (lat_max - lat_min)/2, lon_min + (lon_max - lon_min)/2]

    if click_data is not None:
        clicked_poly = click_data['geometry']['coordinates'][0]
        poly_centre = center_from_polygon(clicked_poly)
        marker = dl.Marker(
            position=poly_centre,
            icon=_custom_icon
        )
        return marker, json.dumps([poly_centre])
    else:
        raise PreventUpdate


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