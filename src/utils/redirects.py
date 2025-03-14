from app import server
from flask import request, redirect
import datetime as dt

HOMEPAGE = '/'
ALLOWED_QUERY_VALUES = {
    'extreme_type': ['hot', 'cold'],
    'method': ['yearmax', 'calendar'],
    'date': {
        'MIN_DATE': dt.date(1940, 1, 1),
        'MAX_DATE': dt.date(2022, 12, 31)
    },
    'loc': []
}

# Redirect incorrect analysis requests back to homepage
@server.before_request
def analysis():
    if request.method == 'GET' and request.path == '/analysis':
        # Check if the query string has an inappropriate amount of parameters
        if len(request.args.keys()) != 5:
            return redirect(HOMEPAGE)
        
        # Check if any query parameter key is unexpected
        if not all([param in ['extreme_type', 'method', 'date', 'loc']\
                        for param in request.args.keys()]):
            return redirect(HOMEPAGE)
        
        # Check if any query parameter is empty
        if '' in request.args.values():
            return redirect(HOMEPAGE)

        # TODO Check each parameter value against a set of allowed values