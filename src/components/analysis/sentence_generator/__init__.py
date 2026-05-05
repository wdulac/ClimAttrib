"""
Sub-package for generating the automated attribution text paragraph.

``automated_text(event, stats, lang)`` (from ``builder``) is the only public
entry point. The template selection logic and the structure of the template
context are documented in ``builder.py``.

Exports:

- ``automated_text`` — the fully automated textual attribution analysis.

Internal modules:

- ``__metrics`` — extracts raw numerical values (pF, pC, PR, FAR, dI, …) from
  the attribution ``xr.Dataset`` for the three time horizons (then/today/future).
- ``__phrases`` — turns those metrics into pre-formatted attribution phrases
  (e.g. "X [A to B] times more likely"), including IPCC bracket notation for
  confidence intervals.
- ``__data_models`` — dataclasses used to pass structured metric bundles between
  the modules above and the template.
- ``__loader`` — loads and caches the Jinja2 templates from
  ``sentence_generator/templates/``.
- ``__text_with_tooltip`` — earlier tooltip-based renderer, not used in the
  current flow.
"""

from .builder import automated_text