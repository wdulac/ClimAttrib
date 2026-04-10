import hmac, hashlib
import os
import time


ADMIN_SECRET = os.getenv("ADMIN_SECRET").encode('utf-8')
HASH = hashlib.sha256


def verify_signature(extra, timestamp, signature, max_age=30):
    """
    Payload = ":timestamp:":":extra:"
    Signature = HMAC(SECRET, Payload)
    """

    if abs(time.time() - int(timestamp)) > max_age:
        return False

    payload = f"{timestamp}:{extra}".encode('utf-8')
    expected = hmac.new(ADMIN_SECRET, payload, HASH).hexdigest()
    
    return hmac.compare_digest(expected, signature)