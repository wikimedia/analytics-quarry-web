import ast
import json
from pymysql.err import OperationalError

from flask import Blueprint, g, Response, request
from sqlalchemy.exc import IntegrityError

from . import worker
from .models.user import UserGroup
from .models.query import Query
from .models.queryrevision import QueryRevision
from .models.queryrun import QueryRun
from .models.star import Star
from .user import get_user, get_preferences
from .utils import valid_dbname

api_blueprint = Blueprint("api", __name__)


@api_blueprint.route("/api/query/unstar", methods=["POST"])
def unstar_query():
    if get_user() is None:
        return "Unauthorized access", 403
    query = g.conn.session.query(Query).get(request.form["query_id"])
    if query:
        star = (
            g.conn.session.query(Star)
            .filter(Star.query_id == request.form["query_id"])
            .filter(Star.user_id == get_user().id)
            .one()
        )
        g.conn.session.delete(star)
        g.conn.session.commit()
        return ""
    else:
        return "Query not found", 404


@api_blueprint.route("/api/query/star", methods=["POST"])
def star_query():
    if get_user() is None:
        return "Unauthorized access", 403
    query = g.conn.session.query(Query).get(request.form["query_id"])
    if query:
        star = Star()
        star.user = get_user()
        star.query = query
        g.conn.session.add(star)
        try:
            g.conn.session.commit()
        except IntegrityError as e:
            if e.args[0] == 1062:  # Duplicate
                g.conn.session.rollback()
            else:
                raise
        return ""
    else:
        return "Query not found", 404


@api_blueprint.route("/api/query/meta", methods=["POST"])
def api_set_meta():
    if get_user() is None:
        return "Authentication required", 401

    query = (
        g.conn.session.query(Query)
        .filter(Query.id == request.form["query_id"])
        .one()
    )

    if query.user_id != get_user().id:
        return "Authorization denied", 403

    if "title" in request.form:
        query.title = request.form["title"]
    if "published" in request.form:
        query.published = request.form["published"] == "1"
    if "description" in request.form:
        query.description = request.form["description"]
    g.conn.session.add(query)
    g.conn.session.commit()
    return json.dumps({"id": query.id})


@api_blueprint.route("/api/query/run", methods=["POST"])
def api_run_query():
    if get_user() is None:
        return "Authentication required", 401
    text = request.form["text"]
    query_database = request.form["query_database"].lower().replace(" ", "")
    query = (
        g.conn.session.query(Query)
        .filter(Query.id == request.form["query_id"])
        .one()
    )
    if not valid_dbname(query_database):
        return "Bad database name", 400

    if (
        query.user_id != get_user().id
        or g.conn.session.query(UserGroup)
        .filter(UserGroup.user_id == get_user().id)
        .filter(UserGroup.group_name == "blocked")
        .first()
    ):
        return "Authorization denied", 403

    # Determine if already run, to update status in case job was killed
    if query.latest_rev and query.latest_rev.latest_run:
        result = worker.run_query.AsyncResult(
            query.latest_rev.latest_run.task_id
        )
        if not result.ready():
            result.revoke(terminate=True)
            query.latest_rev.latest_run.status = QueryRun.STATUS_SUPERSEDED
            g.conn.session.add(query.latest_rev.latest_run)
            g.conn.session.commit()

    query_rev = QueryRevision(
        query_id=query.id, query_database=query_database, text=text
    )
    query.latest_rev = query_rev

    # XXX (phuedx, 2014/08/08): This deviates from the pre-existing
    # QueryRevision interface, but I'm not confident that SQLAlchemy would
    # invalidate a cached result for a relationship if a property changed.
    query_run = QueryRun()
    query_run.rev = query_rev
    query_run.status = QueryRun.STATUS_QUEUED

    g.conn.session.add(query_run)
    g.conn.session.add(query)
    g.conn.session.commit()
    query_rev.latest_run = query_run
    query_run.task_id = worker.run_query.delay(query_run.id).task_id
    g.conn.session.add(query_rev)
    g.conn.session.add(query_run)
    g.conn.session.commit()
    return json.dumps({"qrun_id": query_run.id})


@api_blueprint.route("/api/query/stop", methods=["POST"])
def api_stop_query():
    if get_user() is None:
        return "Authentication required", 401

    qrun_id = request.form["qrun_id"]
    db_of_process = request.form["query_database"]

    # the db process id of the running job is stored in the query_run table while
    # the job is running. We can take this pid over to the database running the
    # query to stop the job
    query_run = (
        g.conn.session.query(QueryRun).filter(QueryRun.id == qrun_id).one()
    )
    result_dictionary = ast.literal_eval(query_run.extra_info)
    if "connection_id" in result_dictionary:
        g.replica.connection = db_of_process
        cur = g.replica.connection.cursor()
        try:
            cur.execute("KILL %s;", (result_dictionary["connection_id"]))
            output = "job stopped"
        except OperationalError:
            output = "job not running"
    else:
        output = "job not running"

    # Stopping the job usually gets a stopped status. However some jobs stopped
    # before the stop button was pressed, and didn't update the DB to reflect
    # this. Cleanup here. Should we make a feature that looks for jobs that have
    # failed, but have not updated the DB to reflect as much, it may be
    # reasonable to update this clause to match the state offered by a cleanup
    # feature ("job lost" or some such)
    query_run.status = QueryRun.STATUS_STOPPED
    g.conn.session.add(query_run)
    g.conn.session.commit()
    return json.dumps({"stopped": output})


@api_blueprint.route("/api/preferences/get/<key>")
def pref_get(key):
    if get_user() is None:
        return "Authentication required", 401

    if key in get_preferences():
        return Response(
            json.dumps({"key": key, "value": get_preferences()[key]}),
            mimetype="application/json",
        )
    else:
        return Response(
            json.dumps({"key": key, "error": "novalue"}),
            mimetype="application/json",
        )


@api_blueprint.route("/api/preferences/set/<key>/<value>")
def pref_set(key, value):
    if get_user() is None:
        return "Authentication required", 401

    get_preferences()[key] = None if value == "null" else value
    return (
        Response(
            json.dumps({"key": key, "success": ""}), mimetype="application/json"
        ),
        201,
    )


@api_blueprint.route("/api/dbs")
def get_dbs():
    known_dbs = (
        g.conn.session.query(QueryRevision.query_database).distinct().all()
    )
    return Response(
        json.dumps(
            {
                "dbs": list(
                    set(
                        db_result[-1].strip()
                        for db_result in known_dbs
                        # the db data might be NULL, empty strings or spaces+tabs only so this helps a bit to show only
                        # likely names
                        if db_result[-1] and db_result[-1].strip()
                    )
                )
            }
        ),
        mimetype="application/json",
    )
