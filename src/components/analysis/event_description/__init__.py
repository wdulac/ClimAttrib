"""
Sub-package for the event description banner displayed above the results carousel.

Exports:
- ``event_description_component`` — the main banner component.

Internal modules:
- ``__event_key_figures`` — builds the row of summary cards (location, date
  range, observed intensity, computation method).
- ``__reverse_geocode`` — resolves lat/lon to a human-readable place name.
- ``__temperature_plot`` — legacy component, not used in the current flow.
"""

from .analysis_description_component import event_description_component