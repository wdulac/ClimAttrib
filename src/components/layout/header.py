from dash import html, dcc
from dash import Output, Input, State, callback, MATCH
from dash_iconify import DashIconify
import dash_mantine_components as dmc

from components.resources import (
    QUICKGUIDE_CONTENT,
    INTERPRETATION_HELP_CONTENT,
    ABOUT_CONTENT,
    DISCLAIMER_CONTENT
)

from app_platform.shared.urls import asset_url, URL_PREFIX_DASH

### Individual header items/buttons

_how_to_use = html.Div(children=[
    dmc.Button(
        "How to use",
        id={"type": "modal-button", "name": "how-to-use"},
        variant='subtle',
        rightSection=DashIconify(icon="fluent:book-question-mark-24-regular", width=28)
    ),
    dmc.Modal(
        title="How to use",
        id={"type": "modal-content", "name": "how-to-use"},
        children=[
            dmc.Tabs([
                # Define the tabs themselves
                dmc.TabsList([
                        dmc.TabsTab("Quick guide", value="quickguide"),
                        dmc.TabsTab("Results interpretation", value="interpretation")
                    ]),
                # Then comes the conent of each tab
                dmc.TabsPanel(
                    dcc.Markdown(QUICKGUIDE_CONTENT),
                    value="quickguide"
                ),
                dmc.TabsPanel(
                    dcc.Markdown(INTERPRETATION_HELP_CONTENT),
                    value="interpretation"
                )
            ],
            # Default tab
            value="quickguide",
            styles={
                'tabLabel': {
                    'fontSize': 18
                }
            }),
        ],
        size='55%',
        styles={
            'title': {
                'fontSize': '32px',
                'fontWeight': 700
            },
        }
    )
])

_about_logo_files = [
    "CNRM.png",
    "CNRS.png",
    "MeteoFrance.png",
    "LSCE.png",
    "CEA.png",
    "IPSL.png",
    "UVSQ.png",
    "France2030.png",
]

_about_logos = [
    html.Div(
        html.Img(
            src=asset_url(f"logos/{filename}"),
            className="about-logo-img",
        ),
        className="about-logo-wrapper",
    )
    for filename in _about_logo_files
]

_about = html.Div(children=[
    dmc.Button(
    "About",
    id={"type": "modal-button", "name": "about"},
    variant="subtle"
    ),
    dmc.Modal(
        id={"type": "modal-content", "name": "about"},
        title="About",
        size="55%",
        styles={
            "title": {
                "fontSize": "32px",
                "fontWeight": 700
            },
        },
        children=[
            dmc.Stack(
                [
                    dcc.Markdown(ABOUT_CONTENT),
                    html.Div(
                        _about_logos,
                        className='about-logos-grid'
                    )
                ],
                gap='lg'
            )
        ]
    )
])


_disclaimer = html.Div(children=[
    dmc.Button(
        'Disclaimer',
        id={"type": "modal-button", "name": "disclaimer"},
        variant='subtle'
    ),
    dmc.Modal(
        id={"type": "modal-content", "name": "disclaimer"},
        title='Disclaimer',
        size='55%',
        styles={
            "title": {
                "fontSize": "32px",
                "fontWeight": 700
            },
        },
        children=dcc.Markdown(DISCLAIMER_CONTENT)
    )
])


_github_action_button = html.A(
    href='https://github.com/wdulac/ClimAttrib',
    target='_blank',
    className='github-logo',
    children=[
        dmc.ActionIcon(
            variant='subtle',
            children=[
                dmc.Image(src=asset_url('logos/github.svg'), w=30)
            ],
            size="lg"
        )
    ]
)

### Grouping buttons in a single item

_header_right = dmc.Group(
    children=dmc.Group(
        children=[
            _how_to_use,
            _about,
            _disclaimer,
            # _language_menu,
            dmc.Space(w='10px'), # For even spacing of the buttons
            _github_action_button
        ], id='header-buttons'
    ), id='header-right'
)

### Composing header with a two-column grid layout

header = html.Header(
    children=[
        dmc.Grid(
            children=[
                dmc.GridCol(
                    children=[
                        html.A(
                            # TODO Restrict clickable zone to the actual title
                            href=URL_PREFIX_DASH,
                            children=html.H1(
                                "WeatherAttrib",
                                id='page-title'
                            ),
                            id='title-anchor'
                        )
                    ],
                    style=None,
                    span=6
                ),
                dmc.GridCol(
                    children=_header_right,
                    style=None,
                    span=6
                )
            ]
        )
    ], className='header-parent'
)


@callback(
    Output({"type": "modal-content", "name": MATCH}, "opened"),
    Input({"type": "modal-button", "name": MATCH}, "n_clicks"),
    State({"type": "modal-content", "name": MATCH}, "opened"),
    prevent_initial_call=True
)
def toggle_modal(n, opened):
    return not opened