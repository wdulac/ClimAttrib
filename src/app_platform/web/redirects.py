"""
URL redirect rules attached as a Flask ``before_request`` hook.

Validates incoming GET requests to ``/analysis`` before they reach Dash, redirecting
to the home page if:

- The ``p`` query parameter is absent.
- There is more than one query parameter.
- The base64-decoded payload is 16 bytes or shorter (a basic length check before the
  full HMAC verification done in ``pages/analysis.py``).

Registered on the Flask server by ``register_redirects(server)`` called from
``app.py``.
"""

from flask import request, redirect
import base64

HOMEPAGE = '/'

def register_redirects(server):

# Redirect incorrect analysis requests back to homepage
    @server.before_request
    def analysis():
        if request.method == 'GET' and request.path == '/analysis':
            # Check if the query string has an inappropriate amount of parameters
            if len(request.args.keys()) != 1:
                return redirect(HOMEPAGE)
            
            if 'p' not in request.args.keys():
                return redirect(HOMEPAGE)

            # Check if parameter is at least 16 bytes long
            p = request.args['p']
            if len(base64.urlsafe_b64decode(p + '=' * (-len(p) % 4))) <= 16:
                return redirect(HOMEPAGE)