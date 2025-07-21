from app import server
from flask import request, Response
import io

from .tasks import attribution

@server.route("/download_csv")
def download_csv():

    task_id = request.args.get("task_id")
    variables = request.args.get("variables")

    if not task_id or not variables:
        return "Missing parameters", 400
    
    task = attribution.AsyncResult(task_id)

    try:
        stats = task.result
    except Exception as e:
        return f"Failed to retrieve task result: {e}", 500
    
    vars = variables.split('_')

    try:
        df = stats[vars].to_dataframe().unstack("quantile")
        df.columns = [f"{var}_{q}" for var, q in df.columns]
        df.reset_index(inplace=True)
    except Exception as e:
        return f"Failed to convert dataset: {e}", 500
    
    csv_io = io.StringIO()
    df.to_csv(csv_io, index=False)
    csv_io.seek(0)

    return Response(
        csv_io, mimetype="text/csv",
        headers={
            "Content-Disposition": f"attachment;filename=plot_data_{variables}.csv"
        }
    )

