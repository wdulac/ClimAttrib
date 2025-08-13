from dash import register_page, html
from components.home.input_settings_top_bar import input_settings_top_bar
from components.home.location_selector import location_selector

register_page(__name__, path='/')

layout = html.Div([
    input_settings_top_bar,
    location_selector
    ], className='home-container'
)