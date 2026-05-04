"""
Application entry point.

Creates the Flask server and the Dash application that sits on top of it, assembles
the top-level page layout (header, footer, disclaimer, page container), then registers
API routes, admin routes, and URL redirect rules on the Flask server.

The module-level ``server`` object (a Flask instance) is the WSGI callable used by
production servers (e.g. ``gunicorn --bind 0.0.0.0:8000 src.app:server``).
For development, run directly with ``python src/app.py`` (settings are read from
``.env`` via ``app_platform.shared.config``).

Import order matters: the ``app_platform.web`` modules must be imported after the
Flask ``server`` object is created, and ``register_disclaimer_callbacks`` must be
called before ``application.layout`` is assigned.
"""

# Utils imports
from app_platform.shared.config import (
    APP_HOST,
    APP_PORT,
    APP_DEBUG,
    APP_SHOW_DASH_DEV_TOOLS,
    URL_PREFIX_DASH,
    PRODUCTION
)
# Essentials
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
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

from app_platform.web import (
    register_redirects,
)
from app_platform.web.api import register_api_routes
from app_platform.web.admin import register_admin_routes

import logging

# Initialize
server = Flask(__name__)

if PRODUCTION:
    server.wsgi_app = ProxyFix(
        server.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
    )

server.logger.setLevel(logging.INFO)

application = Dash(
    server=server,
    url_base_pathname=URL_PREFIX_DASH,
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

    html.Div(children=[
        page_container,
        dmc.Center(
            dmc.Stack(
                [
                    dmc.Loader(size="xl", type="dots"),
                    dmc.Text("The application is loading...", ta="center", size="lg")
                ],
                align="center"
            ),
            id="page-loader"
        )
        ],
        id="page-wrapper"
    ),

    footer
    ], className='site-container'
)

# Avoid circular import of application in src/components/layout/disclaimer.py
register_disclaimer_callbacks(application)

application.layout = dmc.MantineProvider(layout)

# Attach functionnalities (redirection rules and routes) to server
register_api_routes(server)
register_admin_routes(server)
register_redirects(server)

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