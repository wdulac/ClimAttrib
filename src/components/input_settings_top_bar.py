import dash_mantine_components as dmc
from dash import html, callback, Output, Input, State, dcc
from dash.exceptions import PreventUpdate
from .location_selector import *

from datetime import datetime, timedelta, date


TOP_BAR_INPUTS_LABEL_PROPS = {
    'c': 'white',
    'fw': 700,
    'fz': 18,
}


_extreme_type_segmented = dmc.Stack(children=[
    dmc.Text("Type d'extrême", **TOP_BAR_INPUTS_LABEL_PROPS),
    dmc.SegmentedControl(
        id='input:extreme-type',
        data=[
            {"value": "hot", "label": "Chaud"},
            {"value": "cold", "label": "Froid"}
        ],
        value="hot"
    )],
    className='selector-with-label'
)


_computation_method_segmented = dmc.Stack(children=[
    dmc.Text("Méthode de calcul", **TOP_BAR_INPUTS_LABEL_PROPS),
    dmc.SegmentedControl(
        id='input:computation-method',
        data= [
            {"value": "maximum", "label": "Max. annuel"},
            {"value": "calendar", "label": "Calendaire"}
        ],
        value="maximum"
    )],
    className='selector-with-label'
)


_date_selector_calendar = dmc.DatePickerInput(
    id='input:date',
    label="Date de l'évènement",
    labelProps=TOP_BAR_INPUTS_LABEL_PROPS,
    value=date(1994, 11, 8),
    w=250,
    highlightToday=True,
    maxDate=date(2024, 12, 31),
    style=dict(
        zIndex=2
    )
)


_event_duration_slider = dmc.Stack(children=[
    dmc.Text("Durée de l'évènement en jours", **TOP_BAR_INPUTS_LABEL_PROPS),
    dmc.Slider(
        id='input:event-duration',
        value=3,
        min=1,
        max=10,
        restrictToMarks=True,
        marks=[{"value": _, "label": str(_)} for _ in [1, 2, 3, 4, 5, 6, 7, 10]],
        label=None,
        size=10,
        classNames=dict(
            markLabel='duration-slider-markLabel'
        )
    )],
    id='slider-with-label'
)

_continue_button = dmc.Button(
    'Poursuivre',
    size='lg',
    variant='gradient',
    id='trigger:continue-btn'
)
    

debug_style = {
    "border": f"1px solid {dmc.DEFAULT_THEME['colors']['indigo'][4]}",
}

# Laying out all elements
input_settings_top_bar = html.Div(children=[
    html.H5("Définition de l'évènement extrême", id='settings-row-title'),
    dmc.Divider(variant='solid'),
    dmc.Grid(children=[
        dmc.GridCol(children=[
            dmc.Group(children=[
                _extreme_type_segmented,
                _computation_method_segmented,
                _date_selector_calendar,
                _event_duration_slider
                ], id='inputs-row-left')
            ], span=9.5),
        dmc.GridCol(children=[
            dmc.Group(children=[
                html.Div(id='button-notification-container'),
                html.Div(id='dynamic-link')
                ], id='inputs-row-right')
            ], span='auto', id='right-column'),
    ], id='inputs-row')
], className='settings-top-bar')


#~~~~~~~ Callbacks

@callback(
    Output('button-notification-container', 'children'),
    Input('trigger:continue-btn', 'n_clicks'),
    State('input:selected-point', 'data'),
    prevent_initial_call=True
)
def notify_user(n_clicks, selected_point_data):
    if selected_point_data is None:
        return dmc.Notification(
            title="Oups !",
            message="Veuillez sélectionner un point de grille avant de poursuivre",
            action="show",
            autoClose=3500
        )
    else:
        raise PreventUpdate
    
@callback(
    Output('dynamic-link', 'children'),
    Input('input:selected-point', 'data'),
)
def update_link(grid_point):
    print('hello')
    if grid_point is not None:
        return dcc.Link(children=_continue_button, href='/analysis')
    else:
        return _continue_button