from dash import html, dcc
from dash import Output, Input, State, callback
from dash_iconify import DashIconify
import dash_mantine_components as dmc

from utils.paths import RESOURCES


# debug_style = {
    # "border": f"1px solid {dmc.DEFAULT_THEME['colors']['indigo'][4]}",
    # "textAlign": "center"
# }

### Individual header items/buttons

_about_button = html.A(
    href="",
    children=[
        dmc.Button("About", variant='subtle')
    ]
)

QUICKGUIDE_FILE = RESOURCES / 'quickguide.md'
with open(QUICKGUIDE_FILE, 'r') as f:
    QUICKGUIDE_CONTENT = f.read()

INTERPRETATION_HELP_FILE = RESOURCES / 'interpretation_help.md'
with open(INTERPRETATION_HELP_FILE, 'r') as f:
    INTERPRETATION_HELP_CONTENT = f.read()

_how_to_use = html.Div(children=[
    dmc.Button(
        "How to use",
        id='how-to-button',
        variant='subtle',
        rightSection=DashIconify(icon="fluent:book-question-mark-24-regular", width=28)
    ),
    dmc.Modal(
        title="How to use",
        id='how-to-modal',
        children=[
            dmc.Tabs([
                # Define the tabs themselves
                dmc.TabsList([
                        dmc.TabsTab("Quick guide", value="quickguide"),
                        dmc.TabsTab("Results interpration", value="interpretation")
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

# _language_menu = dmc.Menu(
#     children=[
#         dmc.MenuTarget(dmc.Button("EN / FR", variant='subtle')),
#         dmc.MenuDropdown(
#             children=[
#                 dmc.MenuItem(
#                     "English",
#                     href=""
#                 ),
#                 dmc.MenuItem(
#                     "Français",
#                     href=""
#                 )
#             ]
#         )
#     ],
#     trigger='hover',
#     openDelay=100,
#     closeDelay=400,
#     id='language-menu'
# )

_github_action_button = html.A(
    href='https://github.com/wdulac/ClimAttrib',
    target='_blank',
    className='github-logo',
    children=[
        dmc.ActionIcon(
            variant='subtle',
            children=[
                dmc.Image(src='/assets/logos/github.svg', w=30)
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
            _about_button,
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
                            href="/",
                            children=html.H1(
                                "Clim@Attrib",
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
    Output('how-to-modal', 'opened'),
    Input('how-to-button', 'n_clicks'),
    State('how-to-modal', 'opened'),
    prevent_initial_call=True
)
def toggle_how_to_use(n_cliks, opened):
    return not opened