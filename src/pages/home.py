from dash import register_page, html
from components.home.input_settings_top_bar import input_settings_top_bar
from components.home.location_selector import location_selector

register_page(__name__, path='/')

layout = html.Div([
        input_settings_top_bar,
        html.Div(
            [
                location_selector,          # carte
                html.Div(id="home-plots-panel", className="home-plots-panel") # Graphiques
            ],
            className="home-main"
        )
    ],
    className="home-container"
)
