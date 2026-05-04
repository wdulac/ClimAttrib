"""
Home page (route: ``/``).

Registers the Dash home page and defines its layout, composed of:

- ``event_definition_component()`` — the top input bar (date picker, event type,
  computation method, temperature readout, Continue button).
- ``interactive_map_component`` — the Leaflet map for grid cell selection.
- ``#home-plots-panel`` — a collapsible panel that shows contextual plots (annual
  cycle and Yo timeseries) once a location and valid date range are selected.

The layout function is called by Dash each time a user loads the page. All
interactive state is managed through callbacks defined in the component modules
(``components/home/``).
"""

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