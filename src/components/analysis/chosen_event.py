from dash import html
import dash_mantine_components as dmc

def chosen_event(parameters):
    """
    Early prototype for a dynamic component that presents
    the settings chosen by the user
    """
    
    extreme_event = dmc.Table(
        data={
            # "caption": "Event defined with the selected parameters",
            "head": ["Extreme Type", "Computation Method", "Event's date",
                     "Event Duration", "Event intensity", "Latitude", "Longitude"],
            "body": [
                [
                    parameters['extreme_type'],
                    parameters['method'],
                    parameters['date'],
                    parameters['duration'],
                    parameters['event_intensity'] - 273.15,
                    parameters['lat'],
                    parameters['lon']
                 ]

            ]
        },
        highlightOnHover=True,
        withTableBorder=True,
        striped=True,
        style={
            'width': '50%'
        }
    )

    return extreme_event