import os

from flask import Flask, render_template
from flask_mwoauth import MWOAuth


app = Flask(__name__)
app.config.from_pyfile("config.py", silent=False)
app.config['DEBUG'] = True
app.secret_key = 'glkafsjglskhfgflsgkh'

mwoauth = MWOAuth(consumer_key=app.config['OAUTH_CONSUMER_TOKEN'],
                  consumer_secret=app.config['OAUTH_SECRET_TOKEN'])
app.register_blueprint(mwoauth.bp)


@app.route("/static/<path:path>")
def static_proxy(path):
    return app.send_static_file(os.path.join('static', path))


@app.route("/")
def index():
    user = mwoauth.get_current_user()
    return render_template("landing.html", user=user)


@app.route("/query/new")
def new_query():
    user = mwoauth.get_current_user()
    return render_template("query/new.html", user=user)


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
