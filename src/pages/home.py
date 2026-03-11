from dash import register_page, html

from components.home import (
    event_definition_component,
    interactive_map_component
)

register_page(__name__, path='/')

def layout():

    layout = html.Div([
            event_definition_component(),
            html.Div(
                [
                    interactive_map_component,          # carte
                    html.Div(id="home-plots-panel", className="home-plots-panel") # Graphiques
                ],
                className="home-main"
            )
        ],
        className="home-container"
    )

    return layout