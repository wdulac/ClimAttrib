import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash import html, callback, Output, Input

from datetime import datetime, date

_extreme_type_segmented = dmc.Stack(children=[
    dmc.Text("Type d'extrême", c='white', fw=700, fz=18),
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
    dmc.Text("Méthode de calcul", c='white', fw=700, fz=18),
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
    id='input:date',
    label="Date de l'évènement",
    labelProps={
        'c': 'white',
        'fw': 700,
        'fz': 18
    },
    value=datetime.now().date(),
    w=250,
    style=dict(
        zIndex=2
    )
)


_event_duration_slider = dmc.Stack(children=[
    dmc.Text("Durée de l'évènement en jours", c='white', fw=700, fz=18),
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


# Laying out all elements
input_settings_top_bar = html.Div(children=[
    html.H4("Définition de l'évènement extrême", id='settings-row-title'),
    # Note: dmc.Group is a horizontal Flex container
    dmc.Group(children=[
        _extreme_type_segmented,
        _computation_method_segmented,
        _date_selector_calendar,
        _event_duration_slider
        ],
        id='inputs-row'
    )],
    className='settings-top-bar'
)