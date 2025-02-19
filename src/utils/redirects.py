from app import server
from flask import request, redirect

# Redirect incorrect analysis requests back to homepage
@server.before_request
def analysis():
    if request.method == 'GET' and request.path == '/analysis':
        # Check if the query string has an inappropriate amount of parameters
        if len(request.args.keys()) != 5:
            return redirect('/')
        # Check if any query parameter is empty
        if '' in request.args.values():
            return redirect('/')

        # :TODO: Check each query parameter against a set of allowed values