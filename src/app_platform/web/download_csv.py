from flask import request, Response
import io

from app_platform.compute.redis import get_cache
from app_platform.shared.config import URL_PREFIX

CSV_HEADERS = {
    'All': """# This CSV contains the time series data for the selected graph resulting from the attribution analysis.
# Columns are organized as <variable>_<quantile> where :
# - QL = Quantile Low = 5%
# - QU = Quantile Up = 95%
# - BE = Best Estimate
""",

    'pF_pC': """# pF designates the event's yearly probability in the factual world (with human influence).
# pC designates the event's yearly probability in the counterfactual world (without human influence).
# The return period in years can be calculated as 1/p.
""",

    'PR': """# PR designates the probability ratio between the factual world (with human influence) and the counterfactual world (without human influence).
# The fraction of attributable risk, or FAR, can be calculated as 1/(1-PR).
""",

    'IF_IC': """# IF designates the temperature (intensity) of an even with the same probability in the factual world (with human influence).
# IC designates the temperature (intensity) of an even with the same probability in the counterfactual world (without human influence).
# Temperatures are expressed in Kelvin. Conversion to °C can be done by subtracting 273.15.
""",

    'dI': """# dI designates the change in intensity due to human influence for an event with the same probability.
# It is evaluated as the intensity in the factual world (with human influence) minus the intensity in the counterfactual world (without human influence).
"""
}

def register_download_routes(server):

    @server.route(f"{URL_PREFIX}/download_csv")
    def download_csv():

        cache_key = request.args.get("key")
        variables = request.args.get("variables")

        if not cache_key or not variables:
            return "Missing parameters", 400
        
        result = get_cache(cache_key)

        if result['status'] == 'timeout':
            return "Data not available", 500

        stats = result['result']
        
        try:
            df = stats[variables.split('_')].to_dataframe().unstack("quantile")
            df.columns = [f"{var}_{q}" for var, q in df.columns]
            df.reset_index(inplace=True)
        except Exception as e:
            return f"Failed to convert dataset: {e}", 500
        
        csv_io = io.StringIO()

        header = CSV_HEADERS['All'] + CSV_HEADERS[variables]

        csv_io.write(header)

        df.to_csv(csv_io, index=False)
        csv_io.seek(0)

        return Response(
            csv_io, mimetype="text/csv",
            headers={
                "Content-Disposition": f"attachment;filename=plot_data_{variables}.csv"
            }
        )

