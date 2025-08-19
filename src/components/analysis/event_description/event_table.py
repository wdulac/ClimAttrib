from dash import html
import dash_mantine_components as dmc

def debug_table(event):
    """
    Early prototype for a dynamic component that presents
    the settings chosen by the user
    """
    
    extreme_event = html.Div(dmc.Table(
        data={
            "head": ["Extreme Type", "Computation Method", "Event's Date",
                     "Event Duration", "Event intensity", "Latitude", "Longitude"],
            "body": [
                [
                    event['extreme_type'],
                    event['method'],
                    event['date'],
                    event['duration'],
                    f"{event['intensity'] - 273.15:.2f}",
                    event['lat'],
                    event['lon']
                 ]

            ]
        },
        highlightOnHover=True,
        withTableBorder=True,
        striped=True,
        style={
            'width': 'auto'
        }
    ), className='chosen-event')

    return extreme_event