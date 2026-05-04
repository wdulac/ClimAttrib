"""
URL helper functions.

Provides two small utilities that prepend the configured URL prefix
(from ``config.URL_PREFIX``) to relative paths:

- ``asset_url(path)`` — builds a URL pointing to a file under ``/assets/``.
- ``page_url(path)`` — builds a URL pointing to a page route.

Used when constructing ``src`` attributes for images and ``href`` attributes for
links that must remain correct whether the app is served at the root or at a
sub-path (e.g. ``/eventtest/``).
"""

from app_platform.shared.config import URL_PREFIX, URL_PREFIX_DASH

def asset_url(path: str) -> str:
    return f"{URL_PREFIX}/assets/{path.lstrip('/')}"

def page_url(path: str) -> str:
    return f"{URL_PREFIX}/{path.lstrip('/')}"