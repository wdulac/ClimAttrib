from dash import html, callback, Input, Output
from .location_selector import *
import json

coordinates_output = html.Div(
    id='selected-point:output',
)

@callback(
    Output('selected-point:output', 'children'),
    Input('selected-point:input', 'data')
)
def update_text(data):
    if data is not None:
        coords = json.loads(data)[0]
        return f"Coordonées : {coords}"
    else:
        return "En attente de données"
    