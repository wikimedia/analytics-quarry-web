from flask import Flask, render_template, redirect, session, g, request, url_for, Response
from models.user import UserRepository, User
from models.query import QueryRepository, Query
from models.queryrevision import QueryRevisionRepository, QueryRevision
from models.queryrun import QueryRunRepository, QueryRun
import json
import yaml
import time
import os
from sqlalchemy.orm import sessionmaker
from redissession import RedisSessionInterface
from mwoauth import ConsumerToken, Handshaker
from connections import Connections
import worker

__dir__ = os.path.dirname(__file__)

app = Flask(__name__)
app.config.update(yaml.load(open(os.path.join(__dir__, "../default_config.yaml"))))
app.config.update(yaml.load(open(os.path.join(__dir__, "../config.yaml"))))
app.config['DEBUG'] = True
app.session_interface = RedisSessionInterface()

oauth_token = ConsumerToken(
    app.config['OAUTH_CONSUMER_TOKEN'],
    app.config['OAUTH_SECRET_TOKEN']
)


def get_user(user_repository):
    if 'user_id' in session:
        user = user_repository.get_by_id(session['user_id'])
    else:
        user = None
    return user


@app.before_request
def setup_context():
    g.conn = Connections(app.config)

    # Initialise repositories.
    Session = sessionmaker(bind=g.conn.db_engine)
    session = Session()
    g.user_repository = UserRepository(session)
    g.query_repository = QueryRepository(session)
    g.query_revision_repository = QueryRevisionRepository(session)
    g.query_run_repository = QueryRunRepository(session)

    g.user = get_user(g.user_repository)


@app.teardown_request
def kill_context(exception=None):
    g.conn.close_all()


@app.route("/")
def index():
    return render_template("landing.html", user=g.user)


@app.route("/login")
def login():
    handshaker = Handshaker(
        "https://meta.wikimedia.org/w/index.php",
        oauth_token
    )
    redirect_url, request_token = handshaker.initiate()
    session['request_token'] = request_token
    session['return_to_url'] = request.args.get('next', '/')
    return redirect(redirect_url)


@app.route("/oauth-callback")
def oauth_callback():
    handshaker = Handshaker(
        "https://meta.wikimedia.org/w/index.php",
        oauth_token
    )
    access_token = handshaker.complete(session['request_token'], request.query_string)
    session['acces_token'] = access_token
    identity = handshaker.identify(access_token)
    wiki_uid = identity['sub']
    user = g.user_repository.get_by_wiki_uid(wiki_uid)
    if user is None:
        user = User(username=identity['username'], wiki_uid=wiki_uid)
        g.user_repository.save(user)
    session['user_id'] = user.id
    return_to_url = session.get('return_to_url')
    del session['request_token']
    del session['return_to_url']
    return redirect(return_to_url)


@app.route("/query/new")
def new_query():
    if g.user is None:
        return redirect("/login?next=/query/new")
    query = Query()
    query.user = g.user
    query.title = "%s's untitled query #%s" % (g.user.username, int(time.time()))
    g.query_repository.save(query)
    return redirect(url_for('query_show', query_id=query.id))


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/query/<int:query_id>")
def query_show(query_id):
    query = g.query_repository.get_by_id(query_id)
    can_edit = g.user is not None and g.user.id == query.user_id
    jsvars = {
        'query_id': query.id,
        'can_edit': can_edit
    }

    # Check if there's a run?
    latest_rev = g.query_revision_repository.get_latest_by_query(query)
    query_run = g.query_run_repository.get_latest_by_rev(latest_rev)
    if query_run is not None:
        jsvars['output_url'] = url_for('api_query_output', user_id=query.user_id, run_id=query_run.id)

    return render_template(
        "query/view.html",
        user=g.user,
        query=query,
        jsvars=jsvars,
        latest_rev=latest_rev
    )


@app.route('/api/query/output/<int:user_id>/<int:run_id>', methods=['GET'])
def api_query_output(user_id, run_id):
    path = app.config['OUTPUT_PATH_TEMPLATE'] % (user_id, run_id)
    if os.path.exists(path):
        return Response(
            response=open(path).read(),
            status=200,
            headers={
                'Access-Control-Allow-Origin': '*'
            },
            mimetype='application/json'
        )
    else:
        return '', 404


@app.route('/api/query/meta', methods=['POST'])
def api_set_meta():
    if g.user is None:
        return "Authentication required", 401
    query = g.query_repository.get_by_id(request.form['query_id'])
    if 'title' in request.form:
        query.title = request.form['title']
    g.query_repository.save(query)
    return json.dumps({'id': query.id})


@app.route('/api/query/run', methods=['POST'])
def api_run_query():
    if g.user is None:
        return "Authentication required", 401
    text = request.form['text']
    query = g.query_repository.get_by_id(request.form['query_id'])

    last_query_rev = g.query_revision_repository.get_latest_by_query(query)
    if last_query_rev:
        last_query_run = g.query_run_repository.get_latest_by_rev(last_query_rev)
        if last_query_run:
            result = worker.run_query.AsyncResult(last_query_run.task_id)
            if not result.ready():
                result.revoke(terminate=True)
                last_query_run.status = QueryRun.STATUS_SUPERSEDED
                g.query_run_repository.save(last_query_run)
    query_rev = QueryRevision(query_id=query.id, text=text)
    g.query_revision_repository.save(query_rev)
    query.latest_rev_id = query_rev.id
    g.query_repository.save(query)
    query_run = QueryRun()

    # XXX (phuedx, 2014/08/08): This deviates from the pre-existing
    # QueryRevision interface, but I'm not confident that SQLAlchemy would
    # invalidate a cached result for a relationship if a property changed.
    query_run.query_rev_id = query_rev.id
    query_run.status = QueryRun.STATUS_QUEUED
    g.query_run_repository.save(query_run)
    query_run.task_id = worker.run_query.delay(query_run.id).task_id
    g.query_run_repository.save(query_run)
    return json.dumps({
        'output_url': url_for('api_query_output', user_id=g.user.id, run_id=query_run.id)
    })


@app.route("/query/runs/all")
def all_query_runs():
    query_runs = g.query_run_repository.get_latest(25)
    return render_template("query/list.html", user=g.user, query_runs=query_runs)

if __name__ == '__main__':
    app.run(port=5000, host="0.0.0.0")
