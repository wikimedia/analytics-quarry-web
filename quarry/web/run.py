from flask import current_app, Blueprint, g, Response
import json
import sqlite3

from . import output
from .models.queryrun import QueryRun
from .results import SQLiteResultReader
from .utils import json_formatter

run_blueprint = Blueprint("run", __name__)


@run_blueprint.route("/run/<int:qrun_id>/status")
def run_status(qrun_id):
    qrun = g.conn.session.query(QueryRun).get(qrun_id)
    if not qrun:
        return Response("No such query_run id", status=404)
    return Response(
        json.dumps(
            {
                "status": qrun.status_message,
                "extra": json.loads(qrun.extra_info or "{}"),
                "timestamp": qrun.timestamp.strftime("%s"),
            }
        ),
        mimetype="application/json",
        headers={"Access-Control-Allow-Origin": "*"},
    )


@run_blueprint.route(
    "/run/<int:qrun_id>/output/<int:resultset_id>/<string:format>"
)
def output_result(qrun_id, resultset_id=0, format="json"):
    qrun = g.conn.session.query(QueryRun).get(qrun_id)
    if not qrun:
        response = Response("No such query_run id", status=404)
    else:
        reader = SQLiteResultReader(
            qrun, current_app.config["OUTPUT_PATH_TEMPLATE"]
        )
        try:
            response = output.get_formatted_response(
                format, qrun, reader, resultset_id
            )
        except sqlite3.OperationalError as e:
            if e.args[0].startswith("no such table"):
                response = Response("No such resultset id", status=404)
            else:
                raise
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response


@run_blueprint.route("/run/<int:qrun_id>/meta")
def output_run_meta(qrun_id):
    qrun = g.conn.session.query(QueryRun).get(qrun_id)
    if not qrun:
        return Response("No such query run id", status=404)
    return Response(
        json.dumps(
            {"run": qrun, "rev": qrun.rev, "query": qrun.rev.query},
            default=json_formatter,
        ),
        mimetype="application/json",
        headers={"Access-Control-Allow-Origin": "*"},
    )
