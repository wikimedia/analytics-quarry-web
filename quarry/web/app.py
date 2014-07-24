from flask import Flask, render_template, redirect, session, g, request, url_for
from flask_mwoauth import MWOAuth
import oursql
from models.user import User
from models.query import Query, QueryRevision, QueryRun
import json


app = Flask(__name__)
app.config.from_pyfile("../config.py", silent=False)
app.config['DEBUG'] = True
app.secret_key = 'glkafsjglskhfgflsgkh'

mwoauth = MWOAuth(consumer_key=app.config['OAUTH_CONSUMER_TOKEN'],
                  consumer_secret=app.config['OAUTH_SECRET_TOKEN'])
app.register_blueprint(mwoauth.bp)


def get_user():
    if 'user_id' not in session:
        user_name = mwoauth.get_current_user()
        if user_name:
            user_info = mwoauth.request({'action': 'query', 'meta': 'userinfo'})
            wiki_id = user_info['query']['userinfo']['id']
            user = User.get_by_id(wiki_id)
            if user is None:
                user = User(wiki_id, user_name)
                user.save()
            session['user_id'] = user.id
        else:
            user = None
    else:
        user = User.get_by_id(session['user_id'])
    return user


@app.before_request
def setup_context():
    g.conn = oursql.connect(
        host=app.config['DB_HOST'],
        db=app.config['DB_NAME'],
        user=app.config['DB_USER'],
        passwd=app.config['DB_PASSWORD'])
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


@app.route('/api/query/run', methods=['POST'])
def api_run_query():
    if g.user is None:
        return "Authentication required", 401
    print request.form.get('query_rev_id', '')
    query_rev = QueryRevision.get_by_id(request.form['query_rev_id'])
    query_run = QueryRun()
    query_run.query_rev = query_rev
    query_run.save_new()
    return json.dumps({'id': query_run.id})


@app.route("/query/all")
def all_queries():
    user = mwoauth.get_current_user()
    queries = []
    statuses = ['queued', 'running', 'killed', 'done']
    owners = ['yuvipanda', 'halfak', 'J-Mo']
    for i in xrange(25):
        queries.append({
            'id': i,
            'title': 'Random looking query %d' % i,
            'status': statuses[i % 3],
            'owner': owners[i % 2]
        })
    return render_template("query/list.html", user=user, queries=queries)

if __name__ == '__main__':
    app.run(port=6000, host="0.0.0.0")
