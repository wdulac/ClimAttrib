"""
Human-readable formatting of attribution metrics.

Converts raw numerical values (probabilities, return periods, probability
ratios, FAR, temperatures) into display strings with appropriate precision,
threshold-based boundary notation (``< 0.01 %``, ``> 10 000 years``, …), and
unit labels.

Exports:
- ``UNITS`` — dict mapping variable names to their display unit strings.
- ``format_probability`` — probability → percentage string.
- ``format_return_period`` — return period → year string.
- ``format_probability_ratio`` — PR → ratio string.
- ``format_fraction_of_attributable_risk`` — FAR → percentage string.
- ``format_temperature`` — temperature value → string with unit.
"""

from .units import UNITS
from .metrics import (
    format_probability,
    format_return_period,
    format_probability_ratio,
    format_fraction_of_attributable_risk,
    format_temperature
)