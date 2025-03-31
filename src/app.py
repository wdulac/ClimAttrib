# Essentials
from flask import Flask
from dash import Dash, html, page_container
# Bootstrap
import dash_bootstrap_components as dbc
# Mantine
from dash import _dash_renderer
import dash_mantine_components as dmc
_dash_renderer._set_react_version("18.2.0")
# Custom components for the layout
from components import header
from components import footer

# Initialize
server = Flask(__name__)
application = Dash(
    server=server,
    external_stylesheets=[
        # dmc.styles.NOTIFICATIONS,
        # dmc.styles.DATES,
        dbc.themes.BOOTSTRAP # Needed for row and columns to work as expected in dbc
    ],
    update_title=None,
    title="Clim@Ribes",
    suppress_callback_exceptions=True,
    use_pages=True
)


# Define the page layout
layout = html.Div([
    header,
    page_container, # Page content loaded from `pages` folder
    footer
    ], className='site-container'
)

application.layout = dmc.MantineProvider(layout)

# imports from utils need to take place after initialization of the app
from utils import APP_HOST, APP_PORT, APP_DEBUG, APP_SHOW_DASH_DEV_TOOLS
from utils import redirects

# Enable Dash built-in debug tools, even when running with Flask.
# Pro tip : Run with the Flask debugger without this, then toggle the variable.
# Why ? Because then it starts with the flask debugger while also having the Dash tools
if APP_SHOW_DASH_DEV_TOOLS:
    application.enable_dev_tools(
        dev_tools_ui=True,
        dev_tools_serve_dev_bundles=True
    )

if __name__ == "__main__":
    # Note that this is not run when using VSCode debugger
    application.run(
        host=APP_HOST,
        port=APP_PORT,
        debug=APP_DEBUG
    )