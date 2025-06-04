from dash import register_page, html
from components import input_settings_top_bar, location_selector

register_page(__name__, path='/')

layout = html.Div([
    input_settings_top_bar,
    location_selector
    ], className='home-container'
)