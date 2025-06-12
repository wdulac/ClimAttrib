import dash_mantine_components as dmc



def make_skeleton_lines(n, width='100%'):
    return [
        dmc.Skeleton(height=10, radius='xl', w=width if i == n - 1 else '100%')
        for i in range(n)
    ]

loading_screen = dmc.Box([
    dmc.Grid([
        dmc.GridCol([
            dmc.Stack([
                dmc.Skeleton(height=75, circle=True, mb='sm'),
                *make_skeleton_lines(8, width='70%')
            ])
        ], span=6),

        dmc.GridCol([
            dmc.Stack(make_skeleton_lines(12, width='70%'))
        ], span=6)
    ], gutter=100, style={'width': '100%'})
], className='loading-skeleton')