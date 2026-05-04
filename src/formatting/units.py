"""
Unit string functions for formatted metric values.

Exports a ``UNITS`` dict that maps each formatter function from ``metrics.py`` to a
corresponding unit function. Each unit function takes the raw numeric value and
returns the appropriate unit string (handling singular/plural for counts and return
periods).

``UNITS`` is consumed by ``sentence_generator.builder`` and
``science.visualisation.__customdata`` to append the correct unit when building
IPCC-style bracket notation strings.
"""

from .metrics import (
    format_probability,
    format_return_period,
    format_probability_ratio,
    format_fraction_of_attributable_risk,
    format_temperature
)


def unit_percentage(value: float) -> str:
    return "%"


def unit_temperature(value: float) -> str:
    return "°C"


def unit_return_period(value: float) -> str:
    return "year" if value == 1 else "years"


def unit_ratio(value: float) -> str:
    return "time" if value == 1 else "times"


# Map each formatter function to a unit function
UNITS = {
    format_probability: unit_percentage,
    format_return_period: unit_return_period,
    format_probability_ratio: unit_ratio,
    format_fraction_of_attributable_risk: unit_percentage,
    format_temperature: unit_temperature,
}