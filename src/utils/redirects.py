from app import server
from flask import request, redirect

HOMEPAGE = '/'

# Redirect incorrect analysis requests back to homepage
@server.before_request
def analysis():
    if request.method == 'GET' and request.path == '/analysis':
        # Check if the query string has an inappropriate amount of parameters
        if len(request.args.keys()) != 5:
            return redirect(HOMEPAGE)
        
        # Check if any query parameter key is unexpected
        if not all([param in ['extreme_type', 'method', 'date', 'duration', 'loc']\
                        for param in request.args.keys()]):
            return redirect(HOMEPAGE)
        
        # Check if any query parameter is empty
        if '' in request.args.values():
            return redirect(HOMEPAGE)

        # :TODO: Check each parameter value against a set of allowed values