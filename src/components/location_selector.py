from dash import html, callback, Output, Input, State
from dash import dcc
from dash.exceptions import PreventUpdate
import dash_leaflet as dl
import json

ZOOM_LEVEL_THRESHOLD = 4
DEFAULT_ZOOM_LEVEL = 3
MINIMUM_ZOOM_LEVEL = 3
MAP_CENTER_POSITION = [40, 0]
MAP_MAX_BOUNDS = [[-70, -180], [83, -180], [83, 180], [-70, 180]]


_grid = dl.GeoJSON(
    url='/assets/static/grid.geojson',
    style=dict(
        weight=0.5,
        opacity=1,
        color='#066e91',
        fillOpacity=0.1
    ),
    hoverStyle=dict(
        fillOpacity=0.3
    ),
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
            ],
            center=MAP_CENTER_POSITION,
            zoom=DEFAULT_ZOOM_LEVEL,
            minZoom=MINIMUM_ZOOM_LEVEL,
            maxBounds=MAP_MAX_BOUNDS,
            id='map',
            className='map-container'
        ),
        dcc.Store(id='selected-point:input', data=None)
    ],
    className='parent-container'
)
 

#~~~~~~~ Callbacks

@callback(
    Output('grid', 'children'),
    Input('map', 'zoom'),
    State('grid', 'children'),
)
def show_grid(current_zoom_level, grid_state):
    """
    Show the grid passed a certain zoom level
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
        Output("marker", "children"),
        Output("selected-point:input", "data"),
        Input("geojson", "clickData"),
        Input("map", "zoom"),
        State("marker", "children")
)
def place_marker(click_data, zoom_level, marker_state):
    """
    Place marker on the clicked polygon
    """

    def center_from_polygon(coordinates):
        lon_min, lon_max = coordinates[0][0], coordinates[2][0]
        lat_min, lat_max = coordinates[0][1], coordinates[1][1]
        return [lat_min + (lat_max - lat_min)/2, lon_min + (lon_max - lon_min)/2]

    if zoom_level >= ZOOM_LEVEL_THRESHOLD:
        if click_data is not None:
            clicked_poly = click_data['geometry']['coordinates'][0]
            poly_centre = center_from_polygon(clicked_poly)
            marker = dl.Marker(
                position=poly_centre,
                icon=_custom_icon
            )
            return marker, json.dumps([poly_centre])
        else:
            return None, None
    # Handle clearing out the marker when zooming out
    elif marker_state is not None:
        return None, None
    else:
        raise PreventUpdate