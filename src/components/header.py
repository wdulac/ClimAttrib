from dash import html
import dash_mantine_components as dmc


# debug_style = {
    # "border": f"1px solid {dmc.DEFAULT_THEME['colors']['indigo'][4]}",
    # "textAlign": "center"
# }

### Individual header items/buttons

_about_button = html.A(
    href="",
    children=[
        dmc.Button("À propos", variant='subtle')
    ]
)

_language_menu = dmc.Menu(
    children=[
        dmc.MenuTarget(dmc.Button("EN / FR", variant='subtle')),
        dmc.MenuDropdown(
            children=[
                dmc.MenuItem(
                    "English",
                    href=""
                ),
                dmc.MenuItem(
                    "Français",
                    href=""
                )
            ]
        )
    ],
    trigger='hover',
    openDelay=100,
    closeDelay=400,
    id='language-menu'
)

_github_action_button = html.A(
    href='https://github.com/wdulac/EET-app',
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
            _about_button,
            _language_menu,
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
                                "Nom de l'application",
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