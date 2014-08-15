from datetime import datetime
from flask import Flask, render_template, redirect, session, g, request, url_for, Response
from models.user import User
from models.query import Query
from models.queryrevision import QueryRevision
from models.queryrun import QueryRun
from models.star import Star
import json
import yaml
import os
from sqlalchemy import desc, func
from sqlalchemy.orm import sessionmaker, joinedload
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
        user = g.session.query(User).filter(User.id == session['user_id']).one()
    else:
        user = None
    return user


@app.before_request
def setup_context():
    g.conn = Connections(app.config)

    # Initialise repositories.
    Session = sessionmaker(bind=g.conn.db_engine)
    session = Session()
    g.session = session

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
    user = g.session.query(User).filter(User.wiki_uid == wiki_uid).first()
    if user is None:
        user = User(username=identity['username'], wiki_uid=wiki_uid)
        g.session.add(user)
        g.session.commit()
    session['user_id'] = user.id
    return_to_url = session.get('return_to_url')
    del session['request_token']
    del session['return_to_url']
    return redirect(return_to_url)


@app.route('/<string:user_name>')
def user_page(user_name):
    # Munge the user_name, and hope
    user_name = user_name.replace('_', ' ').lower()
    user = g.session.query(User).filter(func.lower(User.username) == user_name).one()
    stats = {
        'query_count': g.session.query(func.count(Query.id)).filter(Query.user_id == user.id).scalar(),
        'stars_count': g.session.query(func.count(Star.id)).filter(Star.user_id == user.id).scalar()
    }
    draft_queries = g.session.query(Query) \
        .filter(Query.user_id == user.id) \
        .filter_by(published=False) \
        .order_by(desc(Query.last_touched)) \
        .limit(10)
    published_queries = g.session.query(Query)\
        .filter(Query.user_id == user.id)\
        .filter_by(published=True)\
        .order_by(desc(Query.last_touched))\
        .limit(10)
    stars = g.session.query(Star).join(Star.query) \
        .options(joinedload(Star.query))\
        .filter(Star.user_id == user.id) \
        .order_by(desc(Star.timestamp))\
        .limit(10)
    return render_template(
        "user.html",
        display_user=user,
        user=g.user,
        stats=stats,
        draft_queries=draft_queries,
        published_queries=published_queries,
        stars=stars
    )


@app.route("/api/query/unstar", methods=["POST"])
def unstar_query():
    if g.user is None:
        return "Unauthorized access", 403
    query = g.session.query(Query).get(request.form['query_id'])
    if query:
        star = g.session.query(Star)\
            .filter(Star.query_id == request.form['query_id'])\
            .filter(Star.user_id == g.user.id)\
            .one()
        g.session.delete(star)
        g.session.commit()
        return ""
    else:
        return "Query not found", 404


@app.route("/api/query/star", methods=["POST"])
def star_query():
    if g.user is None:
        return "Unauthorized access", 403
    query = g.session.query(Query).get(request.form['query_id'])
    if query:
        star = Star()
        star.user = g.user
        star.query = query
        g.session.add(star)
        g.session.commit()
        return ""
    else:
        return "Query not found", 404


@app.route("/query/new")
def new_query():
    if g.user is None:
        return redirect("/login?next=/query/new")
    query = Query()
    query.user = g.user
    g.session.add(query)
    g.session.commit()
    return redirect(url_for('query_show', query_id=query.id))


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/query/<int:query_id>")
def query_show(query_id):
    query = g.session.query(Query).filter(Query.id == query_id).one()
    can_edit = g.user is not None and g.user.id == query.user_id
    is_starred = False
    if g.user:
        is_starred = g.session.query(func.count(Star.id))\
            .filter(Star.user_id == g.user.id)\
            .filter(Star.query_id == query_id).scalar() == 1
    jsvars = {
        'query_id': query.id,
        'can_edit': can_edit,
        'is_starred': is_starred,
        'published': query.published
    }

    if query.latest_rev and query.latest_rev.latest_run:
        query_run = query.latest_rev.latest_run
        jsvars['output_url'] = url_for('api_query_output', user_id=query.user_id, run_id=query_run.id)

    return render_template(
        "query/view.html",
        user=g.user,
        query=query,
        jsvars=jsvars,
        latest_rev=query.latest_rev
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
    query = g.session.query(Query).filter(Query.id == request.form['query_id']).one()
    if 'title' in request.form:
        query.title = request.form['title']
    if 'published' in request.form:
        query.published = request.form['published'] == '1'
    if 'description' in request.form:
        query.description = request.form['description']
    g.session.add(query)
    g.session.commit()
    return json.dumps({'id': query.id})


@app.route('/api/query/run', methods=['POST'])
def api_run_query():
    if g.user is None:
        return "Authentication required", 401
    text = request.form['text']
    query = g.session.query(Query).filter(Query.id == request.form['query_id']).one()

    if query.latest_rev and query.latest_rev.latest_run:
        result = worker.run_query.AsyncResult(query.latest_rev.latest_run.task_id)
        if not result.ready():
            result.revoke(terminate=True)
            query.latest_rev.latest_run.status = QueryRun.STATUS_SUPERSEDED
            g.session.add(query.latest_rev.latest_run)
            g.session.commit()

    query_rev = QueryRevision(query_id=query.id, text=text)
    query.latest_rev = query_rev

    # XXX (phuedx, 2014/08/08): This deviates from the pre-existing
    # QueryRevision interface, but I'm not confident that SQLAlchemy would
    # invalidate a cached result for a relationship if a property changed.
    query_run = QueryRun()
    query_run.rev = query_rev
    query_run.status = QueryRun.STATUS_QUEUED

    g.session.add(query_run)
    g.session.add(query)
    g.session.commit()
    query_rev.latest_run = query_run
    query_run.task_id = worker.run_query.delay(query_run.id).task_id
    g.session.add(query_rev)
    g.session.add(query_run)
    g.session.commit()
    return json.dumps({
        'output_url': url_for('api_query_output', user_id=g.user.id, run_id=query_run.id)
    })


@app.route("/query/runs/all")
def all_query_runs():
    queries = g.session.query(Query)\
        .join(Query.latest_rev).join(QueryRevision.latest_run)\
        .order_by(desc(QueryRun.timestamp))
    return render_template("query/list.html", user=g.user, queries=queries)


@app.template_filter()
def timesince(dt, default="just now"):
    """
    Returns string representing "time since" e.g.
    3 days ago, 5 hours ago etc.

    From http://flask.pocoo.org/snippets/33/
    """

    now = datetime.utcnow()
    diff = now - dt

    periods = (
        (diff.days / 365, "year", "years"),
        (diff.days / 30, "month", "months"),
        (diff.days / 7, "week", "weeks"),
        (diff.days, "day", "days"),
        (diff.seconds / 3600, "hour", "hours"),
        (diff.seconds / 60, "minute", "minutes"),
        (diff.seconds, "second", "seconds"),
    )

    for period, singular, plural in periods:

        if period:
            return "%d %s ago" % (period, singular if period == 1 else plural)

    return default

if __name__ == '__main__':
    app.run(port=5000, host="0.0.0.0")
