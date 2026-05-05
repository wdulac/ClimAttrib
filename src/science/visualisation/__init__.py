"""
Plotly figure builders for the science slides of the results carousel.

Two public modules:

- ``attribution_plots`` — time series charts built from the attribution
  ``xr.Dataset``: probabilities (pF/pC), PR/FAR, intensities (IF/IC), and
  intensity change (ΔI).
- ``climatology_plots`` — observational context charts: the Yo annual-extrema
  timeseries and the daily annual cycle.

Internal modules:

- ``__plotly`` — generic figure builder shared by all attribution charts
  (confidence bands, scenario axis, reference lines).
- ``__customdata`` — builds the Plotly ``customdata`` arrays that populate
  hover tooltips with formatted confidence intervals.
"""

from .attribution_plots import (
    plot_probability,
    plot_PR_FAR,
    plot_intensity,
    plot_intensity_change
)

from .climatology_plots import (
    plot_observed_Yo,
    plot_annual_cycle
)