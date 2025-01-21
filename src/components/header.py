from dash import html, callback, Input, Output
import dash_mantine_components as dmc


debug_style = {
    "border": f"1px solid {dmc.DEFAULT_THEME['colors']['indigo'][4]}",
    "textAlign": "center"
}

header = html.Div(
    children=[
        dmc.Grid(
            children=[
                dmc.GridCol(
                    children=[
                        html.H1("Extreme Event Tracker", id='page-title')
                    ], style=debug_style, span=6
                ),
                dmc.GridCol(
                    children=[
                        dmc.Group(
                            children=[
                                dmc.Text("1"),
                                dmc.Text("2"),
                                dmc.Text("3")
                            ], id="header-right"
                        )
                    ], style=debug_style, span=6
                )
            ]
        )
    ],
    # children=[
    #     html.H1("Extreme Event Tracker", id='page-title')
    # ],
    className='header-parent-div'
)