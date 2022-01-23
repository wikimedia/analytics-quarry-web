from functools import wraps

from flask import request
from prometheus_client.exposition import choose_encoder
from prometheus_client.metrics_core import GaugeMetricFamily
from prometheus_client.registry import CollectorRegistry
from prometheus_flask_exporter import PrometheusMetrics
from sqlalchemy import func

from quarry.web.connections import Connections
from quarry.web.models.queryrun import QueryRun


class QuarryQueryRunStatusCollector:
    def __init__(self, app):
        self.app = app

    def collect(self):
        with Connections(self.app.config).session() as db_session:
            queries_per_status = db_session \
                .query(QueryRun.status, func.count(QueryRun.status)) \
                .group_by(QueryRun.status).all()

        metric_family = GaugeMetricFamily(
            "quarry_query_runs_per_status",
            documentation="Number of query runs per status",
            labels=["status"]
        )

        for (status_id, query_count) in queries_per_status:
            metric_family.add_metric(
                [QueryRun.STATUS_MESSAGES[status_id]],
                query_count
            )

        yield metric_family


def add_custom_metrics(custom_registry: CollectorRegistry):
    """
    Add metrics that we load directly from the database in a way that it works
    even in a 'multiproc' environment like what we do on production with uWSGI.
    """
    def wrapper(f):
        @wraps(f)
        def middleware(*args, **kwargs):
            # Get metrics from the flask exporter
            data, status, headers = f(*args, **kwargs)
            if status != 200:
                return data, status, headers

            # Add our "custom" metrics (like amount of queries per status),
            # without consulting the multiproc handler. Those metrics are
            # generated at /metrics request time, not during normal flask
            # request processing.
            generate_latest, _ = choose_encoder(request.headers.get("Accept"))
            data += generate_latest(custom_registry)

            return data, status, headers

        return middleware

    return wrapper


def metrics_init_app(app):
    if app.config['TESTING']:
        # cheating!! the sqlalchemy mocking system really dislikes
        # how the prometheus collector accesses databases
        return

    custom_registry = CollectorRegistry()
    custom_registry.register(QuarryQueryRunStatusCollector(app))

    # This will automatically use PROMETHEUS_MULTIPROC_DIR if specified,
    # so metrics in production with multiple uwsgi workers work properly.
    # Also note, the prometheus exporter package will not do anything if Flask
    # is in debug mode, unless the env variable DEBUG_METRICS is set.
    metrics = PrometheusMetrics.for_app_factory(
        metrics_endpoint='/metrics',
        metrics_decorator=add_custom_metrics(custom_registry),
        # track metrics per route pattern, not per individual url
        group_by='url_rule',
    )

    metrics.init_app(app)
