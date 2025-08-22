from dash import html, callback, Output, Input, State, dcc
from dash.exceptions import PreventUpdate
import dash_mantine_components as dmc
from dash_iconify import DashIconify

import os
import xarray as xr
import datetime as dt

import json
from utils.url_token import encode_token

TOP_BAR_INPUTS_LABEL_PROPS = {
    'c': 'white',
    'fw': 700,
    'fz': 18,
}

LINK_DEFAULT_HREF = '/'

ALLOWED_DURATIONS = [1, 2, 3, 4, 5, 7, 10] # In days

COMPUTE_TOOLTIP_MD_FILE = 'src/components/home/compute_tooltip_content_usecase.md'
with open(COMPUTE_TOOLTIP_MD_FILE, 'r',encoding='utf-8') as f:
    COMPUTE_TOOLTIP_CONTENT = f.read()


_extreme_type_segmented = dmc.Stack(children=[
    dmc.Text("Extreme type", **TOP_BAR_INPUTS_LABEL_PROPS),
    dmc.SegmentedControl(
        id='input:extreme-type',
        data=[
            {"value": 'hot', "label": "Hot"},
            {"value": 'cold', "label": "Cold"}
        ],
        value='hot',
        persistence=True,
        persistence_type='session',
    )],
    className='selector-with-label'
)


_computation_method_segmented = dmc.Stack(children=[
    dmc.Group(children=[
        dmc.Text("Restrict to same dates", **TOP_BAR_INPUTS_LABEL_PROPS),
        dmc.HoverCard(
            withArrow=True,
            arrowSize=15,
            width=250,
            shadow='md',
            children=[
                dmc.HoverCardTarget(
                    DashIconify(icon="material-symbols:help-outline", width=17,
                    style={"position": "relative", "top": "4px"})
                ),
                dmc.HoverCardDropdown([
                    dcc.Markdown(COMPUTE_TOOLTIP_CONTENT),
                ], className='tooltip-markdown')
            ]
        )
    ], gap='sm'),
    dmc.SegmentedControl(
        id='input:computation-method',
        data= [
            {"value": "calendar", "label": "Yes"},
            {"value": "yearmax", "label": "No"},
        ],
        value="yearmax",
        persistence=True,
        persistence_type='session',
    )],
    className='selector-with-label'
)


_date_selector_calendar = dmc.DatePickerInput(
    id='input:date',
    label="Event date(s)",
    labelProps=TOP_BAR_INPUTS_LABEL_PROPS,
    type='range',
    value=[dt.date(2019, 7, 24), dt.date(2019, 7, 26)],
    allowSingleDateInRange=True,
    w=300,
    highlightToday=False,
    minDate=dt.date(1940, 1, 1),
    maxDate=dt.date(2022, 12, 31),
    persistence=True,
    persistence_type='session',
    disabledDates={"function": "disableInvalidRange", "options": None},
    className='datepicker-container'
)


_continue_button = dcc.Link(
    children=dmc.Button(
        'Continue',
        size='lg',
        variant='gradient',
        id='trigger:continue-btn'
    ),
    href=LINK_DEFAULT_HREF,
    id='dynamic-link'
)
    

_temperature_readout = dmc.Stack(children=[
    dmc.Text("Intensity of the selected event", **TOP_BAR_INPUTS_LABEL_PROPS),
    dmc.Box(id='temp-readout-field', children=None,
            fz=18, c='white', bd='solid white 1px')
], gap=0)


debug_style = {
    "border": f"1px solid {dmc.DEFAULT_THEME['colors']['indigo'][4]}",
}

# Laying out all elements
input_settings_top_bar = html.Div(children=[
    dcc.Store(id='data:intensity', data=None),
    html.H3("Extreme event selection", id='settings-row-title'),
    dmc.Divider(variant='solid'),
    dmc.Grid(children=[
        dmc.GridCol(children=[
            dmc.Group(children=[
                _extreme_type_segmented,
                _date_selector_calendar,
                _computation_method_segmented,
                _temperature_readout
                ], id='left-column')
            ], span=9.5),
        dmc.GridCol(children=[
            _continue_button
        ], span='auto', id='right-column'),
    ], id='inputs-row')
], className='settings-top-bar')


#~~~~~~~ Callbacks

@callback(
    Output('input:date', 'disabledDates'),
    Input('input:date', 'value'),
    prevent_initial_call=True
)
def update_disabled_dates(date_range):
    """
    Pass the current selected dates (even if None) to the JS function that
    decides which date to disable to enforce ALLOWED_DURATIONS.
    
    This is made possible since the DMC 2.0 release
    """

    if date_range:
        return {
            "function": "disableInvalidRange",
            "options": {
                "validDurations": ALLOWED_DURATIONS,
                "startDate": date_range[0],
                "endDate": date_range[1]
            }
        }
    else:
        raise PreventUpdate


@callback(
        Output('input:date', 'error'),
        Input('input:date', 'value'),
        prevent_initial_call=True
)
def calendar_error(dates: list):
    """
    Update the calendar's error property depending on selected date range.
    For the time being (development ungoing), the only valid range length is
    3 days
    """

    try:
        assert sum([isinstance(d, str) for d in dates]) > 0
    except AssertionError:
        # Edge case where you open the calendar, select the start of the range
        # then click out of it. Results in an empty range and dates being
        # [None, None]
        return "Date range cannot be empty"
    else:
        try:
            start, stop = [dt.datetime.strptime(_, '%Y-%m-%d').date()
                            for _ in dates]
        except TypeError:
            # Happens when the date is being picked as the second item in the
            # list is None. This isn't considered an error as the next step
            # is to either select an end date (see below), or click out
            # (see above)
            return ""
        else:
            # At this point we should have a list of two datetime objects.
            # We evaluate the duration in days between start and stop date
            duration = ((stop - start) + dt.timedelta(days=1)).days
            
            if duration not in ALLOWED_DURATIONS:
                return "Please select a valid time range"
            else:
                return ""


@callback(
        Output('temp-readout-field', 'children'),
        Output('data:intensity', 'data'),
        Input('input:selected-point', 'data'),
        Input('input:extreme-type', 'value'),
        Input('input:date', 'value'),
        Input('input:date', 'error')
)
def update_temperature(grid_point: str, extreme_type: str, date: list,
                        date_error) -> str:
    if not None in date:
        if not date_error:
            if grid_point is not None:
                lat, lon = json.loads(grid_point)
                start, stop = [dt.datetime.strptime(_, '%Y-%m-%d').date()
                                for _ in date]
                if extreme_type == 'hot':
                    var = 'tasmax'
                elif extreme_type == 'cold':
                    var = 'tasmin'

                cwd = os.path.basename(os.getcwd())
                if cwd == 'src':
                    path_fix = '../data/daily/'
                elif cwd == 'app' or cwd == 'EET-app':
                    path_fix = './data/daily/'
                
                To = xr.open_dataset(path_fix + f"era5_sfc_{var}_G025.nc")[var].\
                    sel(
                        time=slice(start, stop + dt.timedelta(days=1)),
                        lat=lat, lon=lon % 360
                    ).\
                    mean('time').data
                return f"{To-273.15:.1f}°C", f"{To:.2f}"
            return "Select a grid point", None
        return "Select a valid date range", None
    else:
        return "Select a date range", None


@callback(
    Output('notification-container', 'sendNotifications'),
    Input('trigger:continue-btn', 'n_clicks'),
    State('input:selected-point', 'data'),
    prevent_initial_call=True
)
def notify_user(n_clicks, selected_point_data):
    """
    Notify the user to select a grid point if they try to proceed without
    having selected a grid point.
    """

    if n_clicks:
        if selected_point_data is None:
            return [{
                "action": "show",
                "title": "Oops !",
                "message": "Please select a grid point before proceeding",
                "autoClose": 3500
            }]
        else:
            raise PreventUpdate


@callback(
    Output('dynamic-link', 'href'),
    State('input:selected-point', 'data'),
    Input('input:extreme-type', 'value'),
    Input('input:computation-method', 'value'),
    State('input:date', 'value'),
    Input('input:date', 'error'),
    Input('data:intensity', 'data')
)
def update_link(
    grid_point: str, # JSON serialized
    extreme_type: str,
    computation_method: str,
    date: list,
    date_error: str,
    intensity: str #JSON serialized
) -> str:
    """
    Update the href of the the main button based on the
    selected input settings.
    If no point is selected, the button is made inoperative.
    A valid time range is required to produce a valid href
    """
    if not None in date:
        if not date_error:
            if grid_point is not None:
                # Compose the href based on the input settings
                coords = json.loads(grid_point)
                lat, lon = coords[0], coords[1]
                To = json.loads(intensity)

                # Create signed URL token
                token = encode_token(extreme_type, computation_method, date, lat, lon, To)

                # Create and return href
                href = f"/analysis?p={token}"
                
                return href
            else:
                # If no grid point is selected, revert to default href
                return LINK_DEFAULT_HREF
        return LINK_DEFAULT_HREF
    else:
        return LINK_DEFAULT_HREF