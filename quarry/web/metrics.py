from prometheus_client.metrics_core import GaugeMetricFamily
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


def metrics_init_app(app):
    if app.config['TESTING']:
        # cheating!! the sqlalchemy mocking system really dislikes
        # how the prometheus collector accesses databases
        return

    # This will automatically use PROMETHEUS_MULTIPROC_DIR if specified,
    # so metrics in production with multiple uwsgi workers work properly.
    # Also note, the prometheus exporter package will not do anything if Flask
    # is in debug mode, unless the env variable DEBUG_METRICS is set.
    metrics = PrometheusMetrics.for_app_factory(
        metrics_endpoint='/metrics',
        # track metrics per route pattern, not per individual url
        group_by='url_rule'
    )

    metrics.init_app(app)
    metrics.registry.register(QuarryQueryRunStatusCollector(app))
