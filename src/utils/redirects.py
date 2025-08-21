from app import server
from flask import request, redirect
import base64

HOMEPAGE = '/'

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