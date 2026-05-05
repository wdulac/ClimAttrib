"""
Analysis-page components.

Exports:
- ``results_carousel`` — four-slide carousel: automated text, probability
  charts, intensity charts, observation plots.
- ``event_description_component`` — banner above the carousel summarising the
  event (location, dates, intensity, anomaly) with a back button.
- ``automated_text`` — human-readable attribution analysis generated from
  Jinja2 templates.
"""

from .carousel import results_carousel
from .event_description import event_description_component
from .sentence_generator import automated_text