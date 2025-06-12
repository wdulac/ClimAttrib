from dash.exceptions import PreventUpdate
import dash_mantine_components as dmc


loading_screen = dmc.Box(
    dmc.Grid([
        dmc.GridCol([
            dmc.Stack([
                dmc.Skeleton(height=50, circle=True, mb='xl'),
                dmc.Skeleton(height=8, radius='xl'),
                dmc.Skeleton(height=8, radius='xl'),
                dmc.Skeleton(height=8, radius='xl', w='70%')
            ])
        ], span=6),

        dmc.GridCol([
            dmc.Stack([
                dmc.Skeleton(height=8, radius='xl'),
                dmc.Skeleton(height=8, radius='xl'),
                dmc.Skeleton(height=8, radius='xl'),
                dmc.Skeleton(height=8, radius='xl'),
                dmc.Skeleton(height=8, radius='xl', w='70%')
            ])
        ], span=6),
    ], style={'width': '100%'}),
    className='loading-skeleton'
)