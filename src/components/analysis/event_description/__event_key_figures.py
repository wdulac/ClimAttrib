"""
Key-figure cards for the event description banner.

``key_figures(event)`` builds a row of icon + label + value cards summarising
the event parameters: location with reverse-geocoded country/region, duration
and date range, observed intensity in °C, computation method, and (for the
calendar method) the centred ±1-week seasonal window computed from the event dates.
"""

from dash import html
import dash_mantine_components as dmc
from dash_iconify import DashIconify

from .__reverse_geocode import reverse_lookup
from science.attribution.__calendar_utils import (
    _datetime_to_doy,
    _doy_to_datetime,
    _best_window_from_range
)


def create_stat_card(icon: str, label: str, value: str, icon_style: dict | None=None, extra: str | None=None) -> dmc.Group:
    """Creates a single card for a statistic (icon + text)"""

    extra_line = [dmc.Text(
        extra, size='sm'
    )] if extra else []

    return dmc.Group(
        wrap="nowrap",
        gap='xs',
        align='center',
        children=[
            DashIconify(icon=icon, width=48, color='black', style=icon_style),
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

    intensity_str = f"{event['intensity'] - 273.15:.1f} °C"

    duration_str = f"{event['duration']} days"
    duration_extra_str = (
        f"from {event['start_date'].strftime('%b %d, %Y')} "
        f"to {event['stop_date'].strftime('%b %d, %Y')}"
    )
    
    coords_str = f"{event['lat']} °N; {event['lon']} °E"

    location = reverse_lookup(event['lat'], event['lon'], cell_size=1.5)
    if location:
        location_extra_str = ", ".join([
            location[level] for level in ['country', 'region', 'sub-region'] if location[level]
        ])

    method_str = {
        'yearmax': 'Annual maximum' if event['extreme_type'] == 'hot' else 'Annual minimum',
        'calendar': 'Calendar maximum' if event['extreme_type'] == 'hot' else 'Calendar minimum'
    }.get(event['method'])

    card_list = [
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
            extra=duration_extra_str
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

    if event['method'] == 'calendar':
        ## Evaluate date at the middle of the best calendar window

        # Evaluate calendar window from the date range
        doy1 = _datetime_to_doy(event['start_date'])
        doy2 = _datetime_to_doy(event['stop_date'])
        window_start, _ = _best_window_from_range(doy1, doy2)
        # Evalute date at window center
        window_center = _doy_to_datetime(window_start + 7, event['date'].year)

        ## Create new info card
        time_window_str = f"{window_center.strftime('%b %d')} ± 1 week"

        card_list.append(
            create_stat_card(
                icon="fluent:arrow-maximize-vertical-48-regular",
                icon_style=dict(transform="rotate(90deg)"),
                label="Time window",
                value=time_window_str
            )
        )

    component = html.Div(
        children=[
            dmc.Group(
                justify='space-around',
                gap='3rem',
                children=card_list
            )
        ]
    )

    return component