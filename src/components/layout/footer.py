from dash import html
import dash_mantine_components as dmc

footer = html.Footer(
    children=[
        dmc.Group(
            children=[
                html.Span("© 2026", style=dict(color='white'))
            ], className="footer-row-container"
        ),
    ],
    className='footer-parent'
)