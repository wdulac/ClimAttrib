from dash import dcc, html, Input, Output, State, no_update, ctx
import dash_mantine_components as dmc


def disclaimer_layout():

    return [
        dcc.Store(
            id="disclaimer-store",
            storage_type="local"
        ),

        dmc.Modal(
            id="disclaimer-modal",
            title="Disclaimer",
            children=[
                dcc.Markdown("Placeholder"),
                dmc.Space(h=20),
                html.Div(
                    dmc.Center(
                        dmc.Button(
                            "I understand",
                            id="disclaimer-accept"
                        )
                    ),
                    id="disclaimer-accept-wrapper"
                ),
            ],
            size="55%",
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
        Output("disclaimer-modal", "withCloseButton"),
        Output("disclaimer-modal", "closeOnEscape"),
        Output("disclaimer-modal", "closeOnClickOutside"),
        Output("disclaimer-accept-wrapper", "style"),
        Input("disclaimer-store", "data"),
        Input("disclaimer-accept", "n_clicks"),
        Input("about-button", "n_clicks"),
        State("disclaimer-modal", "opened"),
        prevent_initial_call=False,
    )
    def handle_disclaimer(store_data,
                          accept_clicks,
                          about_clicks,
                          opened):

        trigger = ctx.triggered_id

        # Première visite → modal bloquant
        if trigger == "disclaimer-store" and store_data is None:
            return (
                True,
                no_update,
                False,
                False,
                False,
                {},
            )

        # Clic sur "I understand"
        if trigger == "disclaimer-accept":
            return (
                False,
                {"disclaimer-accepted": True},
                True,
                True,
                True,
                {"display": "none"},
            )

        # Clic sur About → modal normal
        if trigger == "about-button":
            return (
                True,
                no_update,
                True,
                True,
                True,
                {"display": "none"},
            )

        return opened, no_update, no_update, no_update, no_update, no_update