from dash import html, callback, Input, Output, State, ctx, dash_table
from dash.exceptions import PreventUpdate
from .input_settings_top_bar import *
import pandas as pd

trigger_tester = html.Div(
    id='output:button-action',
    style={
        'width': '50%'
    }
)

@callback(
    Output('output:button-action', 'children'),
    Input('trigger:continue-btn', 'n_clicks'),
    # List all of the inputs
    State('input:selected-point', 'data'), # Everything is conditional to this one
    State('input:extreme-type', 'value'),
    State('input:computation-method', 'value'),
    State('input:date', 'value'),
    State('input:event-duration', 'value'),
    prevent_initial_call=True
)
def trigger_button(n_clicks,
                   selected_point_data,
                   extreme_type,
                   computation_method,
                   date,
                   event_duration):

    if selected_point_data is not None:
        IDs = [_.get('id') for _ in ctx.args_grouping[1:]]
        values = [_.get('value') for _ in ctx.args_grouping[1:]]
        out = dict(
            Component_ID=IDs,
            Component_value=values
        )
        df = pd.DataFrame.from_dict(out, orient='index')
        return dash_table.DataTable(data=df.to_dict('records'))
    else:
        raise PreventUpdate