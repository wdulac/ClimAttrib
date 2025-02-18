from dash import register_page, html
from components import input_settings_top_bar, location_selector
from dash_mantine_components import NotificationProvider

register_page(__name__, path='/')

layout = html.Div([
    NotificationProvider(),
    input_settings_top_bar,
    location_selector
    ], className='home-container'
)