from dash import register_page, html

register_page(__name__, path='/analysis')


def layout(extreme_type=None,
           method=None,
           date=None,
           duration=None,
           loc=None,
           **other_unknown_query_strings):

    layout = html.Div([
        html.Div('Bienvenue sur cette page', id='analysis-welcome'),
        ], className='analysis-container'
    )
    return layout