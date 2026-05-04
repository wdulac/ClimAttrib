"""
Infrastructure layer: runtime services and cross-cutting utilities.

Sub-packages:

- ``compute/`` — Celery worker configuration and the ``attribution`` task; Redis
  cache client (DB 1).
- ``shared/`` — utilities that any module in the application can import: runtime
  settings (``config``), project-relative path constants (``paths``), HMAC-signed
  URL tokens (``tokens``), and URL prefix helpers (``urls``). Pages, Dash
  components, science modules, and workers all draw from this sub-package.
- ``web/`` — Flask Blueprint registrations for the public API routes and the
  password-protected admin routes.
"""
