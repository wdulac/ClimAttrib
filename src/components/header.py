from dash import html
import dash_mantine_components as dmc


debug_style = {
    "border": f"1px solid {dmc.DEFAULT_THEME['colors']['indigo'][4]}",
    "textAlign": "center"
}

header = html.Header(
    children=[
        dmc.Grid(
            children=[
                dmc.GridCol(
                    children=[
                        html.H1("Extreme Event Tracker", id='page-title')
                    ], style=None, span=6
                ),
                dmc.GridCol(
                    children=[
                        dmc.Group(
                            children=[
                                dmc.Group(
                                    children=[
                                        html.A(
                                            href="",
                                            children=[
                                                dmc.Button("À propos", variant='subtle')
                                            ]
                                        ),
                                        # dmc.Space(w='xs'),
                                        dmc.Menu(
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
                                        ),
                                        dmc.Space(w='10px'),
                                        html.A(
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
                                    ], id='header-buttons'
                                )
                            ], id="header-right"
                        )
                    ], style=None, span=6
                )
            ]
        )
    ],
    className='header-parent'
)