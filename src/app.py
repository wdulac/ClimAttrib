# Essentials
from flask import Flask
from dash import Dash, dcc, html, page_container
# Mantine
import dash_mantine_components as dmc

# Custom components for the layout
from components.layout import (
    disclaimer_layout,
    register_disclaimer_callbacks
)
from components.layout import(
    header,
    footer
)

# Utils imports
from platform.shared.config import APP_HOST, APP_PORT, APP_DEBUG, APP_SHOW_DASH_DEV_TOOLS

from platform.web import (
    register_redirects,
    register_geojson_routes,
    register_download_routes
)

import locale
import logging

locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

# Initialize
server = Flask(__name__)

server.logger.setLevel(logging.INFO)

application = Dash(
    server=server,
    external_stylesheets=[
        # custom Plotly fullscreen modebar button (Font-Awesome)
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css"
    ],
    external_scripts=[
        # dayjs library for the calendar
        "https://cdnjs.cloudflare.com/ajax/libs/dayjs/1.10.8/dayjs.min.js"
    ],
    update_title=None,
    title="WeatherAttrib",
    suppress_callback_exceptions=True,
    use_pages=True
)


# Define the page layout
layout = html.Div([
    dcc.Location(id='url'),
    dmc.NotificationContainer(id='notification-container'),
    *disclaimer_layout,
    header,
    page_container, # Page content loaded from `pages` folder
    footer
    ], className='site-container'
)

# Avoid circular import of application in src/components/layout/disclaimer.py
register_disclaimer_callbacks(application)

application.layout = dmc.MantineProvider(layout)

# Attach functionnalities (redirection rules and routes) to server
register_redirects(server)
register_geojson_routes(server)
register_download_routes(server)

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