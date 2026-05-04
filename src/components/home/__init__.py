"""
Home-page components.

Exports:
- ``event_definition_component`` — top bar with event type, date, and intensity
  controls, plus the temperature readout.
- ``interactive_map_component`` — Leaflet map for grid-cell selection.
"""

from .input_settings_top_bar import event_definition_component
from .location_selector import interactive_map_component