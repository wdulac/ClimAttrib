"""
HMAC signature verification for admin endpoints.

Admin requests must include two HTTP headers:

- ``Timestamp`` — Unix timestamp (seconds) of the request.
- ``Signature`` — HMAC-SHA256 hex digest of ``"{timestamp}:{route_name}"``, keyed
  with the ``ADMIN_SECRET`` environment variable.

``verify_signature(extra, timestamp, signature, max_age=30)`` returns True only if
the timestamp is within ``max_age`` seconds of now and the signature matches. The
route name (``extra``) is included in the signed payload to prevent a valid signature
for one endpoint from being replayed on another. If ``ADMIN_SECRET`` is not set,
the function always returns False, making all admin endpoints unreachable.
"""

import hmac, hashlib
import os
import time


_admin_secret = os.getenv("ADMIN_SECRET")
ADMIN_SECRET = _admin_secret.encode('utf-8') if _admin_secret else None
HASH = hashlib.sha256


def verify_signature(extra, timestamp, signature, max_age=30):
    """
    Payload = ":timestamp:":":extra:"
    Signature = HMAC(SECRET, Payload)
    """

    if ADMIN_SECRET is None:
        return False

    if abs(time.time() - int(timestamp)) > max_age:
        return False

    payload = f"{timestamp}:{extra}".encode('utf-8')
    expected = hmac.new(ADMIN_SECRET, payload, HASH).hexdigest()

    return hmac.compare_digest(expected, signature)