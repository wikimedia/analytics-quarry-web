import json

from flask import Blueprint, g, Response
from sqlalchemy import text
from .models.query import Query
from .models.queryrun import QueryRun
from .models.queryrevision import QueryRevision

health_blueprint = Blueprint('health', __name__)


def fetch_queries_count_last_minutes(table, column, minutes):
    return g.conn.session.query(table).filter(
        column >= text('NOW() - INTERVAL %d MINUTE' % minutes)
    ).count()


@health_blueprint.route('/.health/summary/v1/<int:minutes>')
def health_summary(minutes):
    """
    Get numbers of Query, QueryRevision, QueryRun happened within
    the last specified `minutes` for monitoring purposes.

    The values returned by this function are most likely always changing
    because every time this API endpoint is accessed it will do some queries
    against the Quarry database to find out how many Query objects are
    created within the last n minutes, etc.
    """
    resp_dict = {}

    resp_dict['queries_num'] = fetch_queries_count_last_minutes(
        Query, Query.last_touched, minutes
    )

    resp_dict['query_revs_num'] = fetch_queries_count_last_minutes(
        QueryRevision, QueryRevision.timestamp, minutes
    )

    statuses = g.conn.session.query(QueryRun.status).filter(
        QueryRun.timestamp >= text('NOW() - INTERVAL %d MINUTE' % minutes)
    ).all()
    resp_dict_query_statuses = {'queued': 0,
                                'failed': 0,
                                'running': 0,
                                'killed': 0,
                                'complete': 0,
                                'superseded': 0}

    for row in statuses:
        query_run_status = row[0]
        resp_dict_query_statuses[
            QueryRun.STATUS_MESSAGES[query_run_status]] += 1

    resp_dict['query_run_statuses'] = resp_dict_query_statuses

    return Response(json.dumps(resp_dict), mimetype='application/json')
