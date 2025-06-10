from dash import html
import dash_mantine_components as dmc

footer = html.Footer(
    children=[
        dmc.Group(
            children=[
                html.A(
                    href="",
                    children="Contact us",
                    className="footer-bottom-link"
                ),
                html.A(
                    href="",
                    children="Privacy policy",
                    className="footer-bottom-link"
                )
            ], className="footer-row-container"
        ),
    ],
    className='footer-parent'
)