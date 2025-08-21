from app import server
from flask import request, redirect

HOMEPAGE = '/'

# Redirect incorrect analysis requests back to homepage
@server.before_request
def analysis():
    if request.method == 'GET' and request.path == '/analysis':
        # Check if the query string has an inappropriate amount of parameters
        if len(request.args.keys()) != 1:
            return redirect(HOMEPAGE)
        
        # Check if any query parameter is empty
        if '' in request.args.values():
            return redirect(HOMEPAGE)