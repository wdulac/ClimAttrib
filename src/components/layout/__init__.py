"""
Page-chrome components rendered on every page.

Exports:
- ``header`` — top navigation bar with logo and links.
- ``footer`` — bottom bar with credits and external links.
- ``disclaimer_layout`` — legal disclaimer modal (shown on first visit).
- ``register_disclaimer_callbacks`` — registers the open/close callbacks for
  the disclaimer modal.
"""

from .header import header
from .footer import footer
from .disclaimer import (disclaimer_layout, register_disclaimer_callbacks)