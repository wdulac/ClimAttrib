"""
Event description banner — displayed above the results carousel on the analysis page.

``event_description_component(event)`` returns a styled panel (``dmc.Paper``) with:

- A row of key-figure cards from ``__event_key_figures.key_figures(event)``
  summarising location (lat/lon + reverse-geocoded place name), duration and date
  range, observed intensity in °C, computation method, and (for the calendar method)
  the ±1-week seasonal comparison window.
- A "Back to event selection" button that navigates back to the home page.

The back button is disabled while computation is in progress (driven by the
``is-loading`` store) and re-enabled once results are available.
"""

from dash import html, callback, Input, Output
from dash.exceptions import PreventUpdate
import dash_mantine_components as dmc

from app_platform.shared.urls import URL_PREFIX_DASH

from .__event_key_figures import key_figures


_back_button = dmc.Button(
    'Back to event selection',
    size='lg',
    loading=False,
    disabled=True,
    variant='gradient',
    id='back-button',
    style={
        'margin-left': 'auto',
        'margin-right': '1rem' # Extra space to add on top of the inline padding
    }
)


def event_description_component(event: dict) -> html.Div:
    """
    Compose complete bar above carousel, with event description + back button
    """

    component = dmc.Paper(
        withBorder=True,
        p='md',
        children=[
            dmc.Group(
                children=[
                    key_figures(event),
                    _back_button
                ],
                grow=False,
                justify='space-around',
                wrap='nowrap'
            )
        ],
        id='event-description-container',
        style={
            "padding-block": "5px",
            "padding-inline": "3rem",
        }
    )

    return component



@callback(
    Output('url', 'href'),
    Input('back-button', 'n_clicks'),
    prevent_initial_call=True
)
def go_home(_):

    if _:
        return URL_PREFIX_DASH
    else:
        raise PreventUpdate
    

@callback(
    # Output('back-button', 'loading'),
    Output('back-button', 'disabled'),
    Input('is-loading', 'data'),
    prevent_initial_callback=False
)
def toggle_back_button_loading(is_loading):
    return is_loading