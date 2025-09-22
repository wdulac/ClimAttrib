from dash import html, callback, Input, Output
from dash.exceptions import PreventUpdate
import dash_mantine_components as dmc

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


def description(event: dict) -> html.Div:
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
        return "/"
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