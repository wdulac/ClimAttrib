from dash import html
import dash_mantine_components as dmc
from dash_iconify import DashIconify

from .shp_reverse_geocode import reverse_lookup


def create_stat_card(icon: str, label: str, value: str, extra: str | None=None) -> dmc.Group:
    """Creates a single card for a statistic (icon + text)"""

    extra_line = [dmc.Text(
        extra, size='sm'
    )] if extra else []

    return dmc.Group(
        wrap="nowrap",
        gap='xs',
        align='center',
        children=[
            DashIconify(icon=icon, width=48, color='black'),
            dmc.Stack(
                gap=0,
                children=[
                    dmc.Text(label, size='md', c='dimmed'),
                    dmc.Text(value, size='xl', fw=600)
                ] + extra_line
            )
        ]
    )


def key_figures(event: dict):
    """
    Assemble cards to describe event selected by the user
    """

    intensity_str = f"{event['intensity'] - 273.15:.2f} °C"
    duration_str = f"{event['duration']} days"
    coords_str = f"{event['lat']} N; {event['lon']} E"

    location = reverse_lookup(event['lat'], event['lon'])
    if location:
        location_extra_str = ", ".join([
            location[level] for level in ['country', 'region', 'sub-region'] if location[level]
        ])

    method_str = {
        'yearmax': 'Annual maximum',
        'calendar': 'Calendar lock-in'
    }.get(event['method'])

    component = html.Div(
        children=[
            dmc.Group(
                justify='space-around',
                gap='3rem',
                children=[
                    create_stat_card(
                        icon="fluent:location-48-regular",
                        label="Location",
                        value=coords_str,
                        extra=location_extra_str
                    ),
                    create_stat_card(
                        icon="fluent:calendar-48-regular",
                        label="Duration",
                        value=duration_str,
                        extra=f"from {event['date']}"
                    ),
                    create_stat_card(
                        icon="fluent:braces-variable-48-regular",
                        label="Variable",
                        value="Maximum temperature"
                    ),
                    create_stat_card(
                        icon="fluent:temperature-48-regular",
                        label="Intensity",
                        value=intensity_str
                    ),
                    create_stat_card(
                        icon="fluent:calendar-settings-48-regular",
                        label="Method",
                        value=method_str
                    ),
                ]
            )
        ]
    )

    return component