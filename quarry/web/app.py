from flask import Flask, render_template, redirect, session, g, request, url_for
from flask_mwoauth import MWOAuth
import pymysql
from models.user import User
from models.query import Query, QueryRevision, QueryRun
from models.queryresult import QuerySuccessResult, QueryErrorResult, QueryKilledResult
import json
import time
import os
import redis
from celery import Celery
from celery.exceptions import SoftTimeLimitExceeded
from redissession import RedisSessionInterface


app = Flask(__name__)
app.config.from_pyfile("../default_config.py", silent=False)
app.config.from_pyfile("../config.py", silent=False)
app.config['DEBUG'] = True
app.secret_key = 'glkafsjglskhfgflsgkh'
app.session_interface = RedisSessionInterface()

mwoauth = MWOAuth(consumer_key=app.config['OAUTH_CONSUMER_TOKEN'],
                  consumer_secret=app.config['OAUTH_SECRET_TOKEN'])
app.register_blueprint(mwoauth.bp)


def make_celery(app):
    celery = Celery('quarry.web.app', broker=app.config['CELERY_BROKER_URL'])
    celery.conf.update(app.config)
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                setup_redis()
                setup_db()
                setup_replica()
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask
    return celery

celery = make_celery(app)


def make_result(cur):
    if cur.description is None:
        return None
    return {
        'headers': [c[0] for c in cur.description],
        'rows': cur.fetchall()
    }


@celery.task
def kill_query(thread_id):
    cur = g.replica.cursor()
    try:
        cur.execute("KILL QUERY %s", thread_id)
    except pymysql.InternalError as e:
        if e.args[0] == 1094:  # Error code for 'no such thread'
            print 'Query already killed'
        else:
            raise
    finally:
        cur.close()


@celery.task
def run_query(query_run_id):
    qrun = QueryRun.get_by_id(query_run_id)
    try:
        qrun = QueryRun.get_by_id(query_run_id)
        qrun.status = QueryRun.STATUS_RUNNING
        qrun.save()
        start_time = time.clock()
        cur = g.replica.cursor()
        try:
            cur.execute(qrun.query_rev.text)
            result = []
            result.append(make_result(cur))
            while cur.nextset():
                result.append(make_result(cur))
            total_time = time.clock() - start_time
            qresult = QuerySuccessResult(qrun, total_time, result, app.config['OUTPUT_PATH_TEMPLATE'])
            qrun.status = QueryRun.STATUS_COMPLETE
        except pymysql.DatabaseError as e:
            total_time = time.clock() - start_time
            qresult = QueryErrorResult(qrun, total_time, app.config['OUTPUT_PATH_TEMPLATE'], e.args[1])
            qrun.status = QueryRun.STATUS_FAILED
        finally:
            cur.close()
        qresult.output()
        qrun.save()
    except SoftTimeLimitExceeded:
        total_time = time.clock() - start_time
        kill_query.delay(g.replica.thread_id())
        qrun.state = QueryRun.STATUS_KILLED
        qrun.save()
        qresult = QueryKilledResult(qrun, total_time, app.config['OUTPUT_PATH_TEMPLATE'])
        qresult.output()


def get_user():
    if 'user_id' not in session:
        user_name = mwoauth.get_current_user()
        if user_name:
            user_info = mwoauth.request({'action': 'query', 'meta': 'userinfo'})
            wiki_id = user_info['query']['userinfo']['id']
            user = User.get_by_wiki_id(wiki_id)
            if user is None:
                user = User(username=user_name, wiki_id=wiki_id)
                user.save_new()
            session['user_id'] = user.id
        else:
            user = None
    else:
        user = User.get_by_id(session['user_id'])
    return user


@app.before_request
def setup_context():
    setup_redis()
    setup_db()
    setup_user()


def setup_redis():
    g.redis = redis.StrictRedis(
        host=app.config['REDIS_HOST'],
        port=app.config['REDIS_PORT'],
        db=app.config['REDIS_DB']
    )


def setup_replica():
    g.replica = pymysql.connect(
        host=app.config['REPLICA_HOST'],
        db=app.config['REPLICA_DB'],
        user=app.config['REPLICA_USER'],
        passwd=app.config['REPLICA_PASSWORD'],
        port=app.config['REPLICA_PORT'],
        charset='utf8'
    )


def setup_db():
    g.conn = pymysql.connect(
        host=app.config['DB_HOST'],
        db=app.config['DB_NAME'],
        user=app.config['DB_USER'],
        passwd=app.config['DB_PASSWORD'],
        autocommit=True,
        charset='utf8'
    )


def setup_user():
    g.user = get_user()


@app.route("/")
def index():
    return render_template("landing.html", user=g.user)


@app.route("/query/new")
def new_query():
    if g.user is None:
        return redirect("/login?next=/query/new")
    query = Query()
    query.user = g.user
    query.title = "%s's awesome query #%s" % (g.user.username, int(time.time()))
    query.save_new()
    return redirect(url_for('query_show', query_id=query.id))


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


@app.route('/api/query/new', methods=['POST'])
def api_new_query():
    if g.user is None:
        return "Authentication required", 401
    text = request.form['text']
    query = Query.get_by_id(request.form['query_id'])
    query_rev = QueryRevision(query_id=query.id, text=text)
    query_rev.save_new()
    query.latest_rev = query_rev
    query.save()
    return json.dumps({'id': query_rev.id})


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
    query_rev = QueryRevision.get_by_id(request.form['query_rev_id'])
    query_run = QueryRun()
    query_run.query_rev = query_rev
    query_run.save_new()
    run_query.delay(query_run.id)
    return json.dumps({
        'output_url': url_for('api_query_output', user_id=g.user.id, run_id=query_run.id)
    })


@app.route("/query/runs/all")
def all_query_runs():
    query_runs = QueryRun.get_augmented_list()
    return render_template("query/list.html", user=g.user, query_runs=query_runs)

if __name__ == '__main__':
    app.run(port=6000, host="0.0.0.0")
