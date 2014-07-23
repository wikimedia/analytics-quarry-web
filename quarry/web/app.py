from flask import Flask, render_template, redirect, session, g
from flask_mwoauth import MWOAuth
import oursql
from models.user import User


app = Flask(__name__)
app.config.from_pyfile("../config.py", silent=False)
app.config['DEBUG'] = True
app.secret_key = 'glkafsjglskhfgflsgkh'

mwoauth = MWOAuth(consumer_key=app.config['OAUTH_CONSUMER_TOKEN'],
                  consumer_secret=app.config['OAUTH_SECRET_TOKEN'])
app.register_blueprint(mwoauth.bp)


def get_user():
    if 'user_id' in session:
        return User.get_by_id(session['user_id'])
    else:
        return None


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


@app.route("/login/done")
def login_done():
    user_name = mwoauth.get_current_user()
    user_info = mwoauth.request({'action': 'query', 'meta': 'userinfo'})
    wiki_id = user_info['query']['userinfo']['id']
    user = User.get_by_id(wiki_id)
    if user is None:
        user = User(wiki_id, user_name)
        User.save(user)
    session['user_id'] = user.id
    return redirect("/")


@app.route("/query/new")
def new_query():
    return render_template("query/new.html", user=g.user)


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
