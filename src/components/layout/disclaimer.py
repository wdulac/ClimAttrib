from dash import dcc, Input, Output, no_update, ctx
import dash_mantine_components as dmc

from components.resources import DISCLAIMER_CONTENT

disclaimer_layout = [
    dcc.Store(
        id="disclaimer-store",
        storage_type="local"
    ),

    dmc.Modal(
        id="disclaimer-modal",
        title="Disclaimer",
        children=[
            dmc.Stack(
                [
                    dcc.Markdown(DISCLAIMER_CONTENT),
                    dmc.Space(h=10),
                    dmc.Center(
                        dmc.Button(
                            "I understand",
                            id="disclaimer-accept"
                        )
                    ),
                ],
                justify="space-between",
                style={"minHeight": 234},
            )
        ],
        centered=True,
        size="55%",
        withCloseButton=False,
        closeOnEscape=False,
        closeOnClickOutside=False,
        transitionProps={"duration": 0},  # ouverture instantanée
        overlayProps={"blur": 8},         # flou permanent
        styles={
            "title": {
                "fontSize": "32px",
                "fontWeight": 700
            },
        },
    ),
]


def register_disclaimer_callbacks(app):

    @app.callback(
        Output("disclaimer-modal", "opened"),
        Output("disclaimer-store", "data"),
        Input("disclaimer-store", "data"),
        Input("disclaimer-accept", "n_clicks"),
        prevent_initial_call=False,
    )
    def handle_disclaimer(store_data, accept_clicks):
        """
        Controls the blocking disclaimer modal.

        Opens the modal on first visit and persists user acceptance.
        The modal cannot be closed except by clicking "I understand".
        """

        trigger = ctx.triggered_id

        # Première visite
        if trigger == "disclaimer-store" and store_data is None:
            return True, no_update

        # Acceptation
        if trigger == "disclaimer-accept":
            return False, {"disclaimer-accepted": True}

        return no_update, no_update