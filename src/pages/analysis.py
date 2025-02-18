from dash import register_page, html

register_page(__name__, path='/analysis')

layout = html.Div([
    html.Div('Bienvenue sur cette page', id='analysis-welcome')
    ], className='analysis-container'
)