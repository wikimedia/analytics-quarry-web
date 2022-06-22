import os

from flask import current_app, Flask, render_template, g
import yaml

from .connections import Connections
from .replica import Replica
from .login import auth
from .metrics import metrics_init_app
from .redissession import RedisSessionInterface
from .user import user_blueprint, get_user
from .utils import monkey as _unused  # noqa: F401
from .health import health_blueprint
from .query import query_blueprint
from .run import run_blueprint
from .api import api_blueprint
from .webhelpers import templatehelpers

__dir__ = os.path.dirname(__file__)


def get_config():
    conf = {}
    conf.update(
        yaml.safe_load(open(os.path.join(__dir__, "../default_config.yaml")))
    )
    try:
        conf.update(
            yaml.safe_load(open(os.path.join(__dir__, "../config.yaml")))
        )
    except IOError:
        # Is ok if we can't load config.yaml
        pass

    return conf


def setup_context():
    g.conn = Connections(current_app.config)
    g.replica = Replica(current_app.config)


def kill_context(exception=None):
    g.conn.close_all()
    del g.replica.connection


def create_app(test_config=None):
    app = Flask(__name__)

    if test_config is None:
        app.config.update(get_config())
    else:
        app.config.from_mapping(test_config)

    app.register_blueprint(auth)
    app.register_blueprint(health_blueprint)
    app.register_blueprint(user_blueprint)
    app.register_blueprint(query_blueprint)
    app.register_blueprint(run_blueprint)
    app.register_blueprint(api_blueprint)
    app.register_blueprint(templatehelpers)

    global_conn = Connections(app.config)
    app.session_interface = RedisSessionInterface(global_conn.redis)

    app.before_request(setup_context)
    app.teardown_request(kill_context)

    metrics_init_app(app)

    @app.route("/")
    def index():
        return render_template("landing.html", user=get_user())

    return app


if __name__ == "__main__":
    application = create_app()
    application.run(port=5000, host="0.0.0.0")
