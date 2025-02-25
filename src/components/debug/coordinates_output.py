from dash import html, callback, Input, Output
from ..home.location_selector import *
import json

coordinates_output = html.Div(
    id='output:selected-point',
)

@callback(
    Output('output:selected-point', 'children'),
    Input('input:selected-point', 'data')
)
def update_text(data):
    if data is not None:
        coords = json.loads(data)[0]
        return f"Coordonées : {coords}"
    else:
        return "En attente de données"
    