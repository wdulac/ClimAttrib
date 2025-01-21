import dash_mantine_components as dmc
from dash import html, callback, Output, Input

from datetime import datetime


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
            "Chaud",
            "Froid"
        ],
        value="Chaud"
    )],
    className='selector-with-label'
)


_computation_method_segmented = dmc.Stack(children=[
    dmc.Text("Méthode de calcul", **TOP_BAR_INPUTS_LABEL_PROPS),
    dmc.SegmentedControl(
        id='input:computation-method',
        data=[
            "Max. annuel",
            "Calendaire"
        ],
    )],
    className='selector-with-label'
)


_date_selector_calendar = dmc.DatePickerInput(
    # :TODO: 
    # Make it so it is not possible to select a date in the future
    id='input:date',
    label="Date de l'évènement",
    labelProps=TOP_BAR_INPUTS_LABEL_PROPS,
    value=datetime.now().date(),
    w=250,
    style=dict(
        zIndex=2
    )
)


_event_duration_slider = dmc.Stack(children=[
    dmc.Text("Durée de l'évènement en jours", **TOP_BAR_INPUTS_LABEL_PROPS),
    dmc.Slider(
        id='duration-slider',
        value=3,
        min=1,
        max=7,
        restrictToMarks=True,
        marks=[{"value": _, "label": str(_)} for _ in range(1, 8)],
        label=None,
        size=10,
        classNames=dict(
            markLabel='duration-slider-markLabel'
        )
    )],
    id='slider-with-label'
)

debug_style = {
    "border": f"1px solid {dmc.DEFAULT_THEME['colors']['indigo'][4]}",
}

# Laying out all elements
input_settings_top_bar = html.Div(children=[
    html.H4("Définition de l'évènement extrême", id='settings-row-title'),
    dmc.Divider(variant='solid'),
    dmc.Grid(children=[
        dmc.GridCol(children=[
            dmc.Group(children=[
                _extreme_type_segmented,
                _computation_method_segmented,
                _date_selector_calendar,
                _event_duration_slider
                ], id='inputs-row-left')
            ],  span=9.5),
        dmc.GridCol(children=[
            dmc.Group(children=[
                dmc.Button('Poursuivre', size='lg', variant='gradient')
            ], id='inputs-row-right')],
            span='auto', id='right-column'),
    ], id='inputs-row')
], className='settings-top-bar')