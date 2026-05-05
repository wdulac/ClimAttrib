"""
Core attribution algorithm sub-package.

``attribute_event(event)`` (from ``event_attribution``) is the only public
entry point; its full pipeline is documented in ``event_attribution.py``.

Internal modules:

- ``__settings`` — scientific parameters (number of MCMC samples, chain size,
  confidence interval level, active scenario, Stan mode, master seed).
- ``__data_loading`` — reads prior distributions from ``data/prior/`` and
  observation timeseries from ``data/Yo/``.
- ``__calendar_utils`` — day-of-year helpers using the application's DOY
  convention (DOY 60 permanently reserved for Feb 29).
"""

from .event_attribution import attribute_event