# Essentials
from flask import Flask
from dash import Dash, html
# App settings
from utils.settings import APP_HOST, APP_PORT, APP_DEBUG, APP_SHOW_DASH_DEV_TOOLS
# Bootstrap
import dash_bootstrap_components as dbc
# Mantine
from dash import _dash_renderer
import dash_mantine_components as dmc
_dash_renderer._set_react_version("18.2.0")
# Custom components for the layout
from components import location_selector
# from components import coordinates_output as selected_point
from components import input_settings_top_bar
from components import trigger_tester
from components import header

# Initialize
server = Flask(__name__)
application = Dash(
    server=server,
    external_stylesheets=[
        dmc.styles.NOTIFICATIONS,
        dmc.styles.DATES,
        dbc.themes.BOOTSTRAP # Needed for row and columns to work as expected in dbc
    ]
)

# Define the page layout
layout = html.Div([
    dmc.NotificationProvider(),
    header,
    input_settings_top_bar,
    location_selector,
    trigger_tester
    ]
)

application.layout = dmc.MantineProvider(layout)

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