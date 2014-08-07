from flask import Flask, render_template, redirect, session, g, request, url_for
from models.user import User
from models.query import Query, QueryRevision, QueryRun
import json
import yaml
import time
import os
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


def get_user():
    if 'user_id' in session:
        user = User.get_by_id(session['user_id'])
    else:
        user = None
    return user


@app.before_request
def setup_context():
    g.conn = Connections(app.config)
    g.user = get_user()


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
    user = User.get_by_wiki_uid(wiki_uid)
    if user is None:
        user = User(username=identity['username'], wiki_uid=wiki_uid)
        user.save_new()
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
    query.save_new()
    return redirect(url_for('query_show', query_id=query.id))


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/query/<int:query_id>")
def query_show(query_id):
    query = Query.get_by_id(query_id)
    can_edit = g.user is not None and g.user.id == query.user_id
    jsvars = {
        'query_id': query.id,
        'can_edit': can_edit
    }

    # Check if there's a run?
    query_run = QueryRun.get_latest_run(query.latest_rev_id)
    if query_run is not None:
        jsvars['output_url'] = url_for('api_query_output', user_id=query.user_id, run_id=query_run.id)

    return render_template(
        "query/view.html",
        user=g.user,
        query=query,
        jsvars=jsvars
    )


@app.route('/api/query/output/<int:user_id>/<int:run_id>', methods=['GET'])
def api_query_output(user_id, run_id):
    path = app.config['OUTPUT_PATH_TEMPLATE'] % (user_id, run_id)
    if os.path.exists(path):
        return open(path).read()
    else:
        return '', 404


@app.route('/api/query/meta', methods=['POST'])
def api_set_meta():
    if g.user is None:
        return "Authentication required", 401
    query = Query.get_by_id(request.form['query_id'])
    if 'title' in request.form:
        query.title = request.form['title']
    query.save()
    return json.dumps({'id': query.id})


@app.route('/api/query/run', methods=['POST'])
def api_run_query():
    if g.user is None:
        return "Authentication required", 401
    text = request.form['text']
    query = Query.get_by_id(request.form['query_id'])

    last_query_rev = query.latest_rev
    if last_query_rev:
        last_query_run = QueryRun.get_latest_run(last_query_rev.id)
        if last_query_run:
            result = worker.run_query.AsyncResult(last_query_run.task_id)
            if not result.ready():
                result.revoke(terminate=True)
                last_query_run.status = QueryRun.STATUS_SUPERSEDED
                last_query_run.save()
    query_rev = QueryRevision(query_id=query.id, text=text)
    query_rev.save_new()
    query.latest_rev = query_rev
    query.save()
    query_run = QueryRun()
    query_run.query_rev = query_rev
    query_run.status = QueryRun.STATUS_QUEUED
    query_run.save_new()
    query_run.task_id = worker.run_query.delay(query_run.id).task_id
    query_run.save()
    return json.dumps({
        'output_url': url_for('api_query_output', user_id=g.user.id, run_id=query_run.id)
    })


@app.route("/query/runs/all")
def all_query_runs():
    query_runs = QueryRun.get_augmented_list()
    return render_template("query/list.html", user=g.user, query_runs=query_runs)

if __name__ == '__main__':
    app.run(port=5000, host="0.0.0.0")
