from flask import Blueprint, request, session, redirect, g
from mwoauth import ConsumerToken, Handshaker
from .models.user import User

auth = Blueprint('auth', __name__)

oauth_token = None


@auth.record
def record_oauth_token(state):
    global oauth_token
    oauth_token = ConsumerToken(
        state.app.config['OAUTH_CONSUMER_TOKEN'],
        state.app.config['OAUTH_SECRET_TOKEN']
    )


@auth.route("/login")
def login():
    handshaker = Handshaker(
        "https://meta.wikimedia.org/w/index.php",
        oauth_token
    )
    redirect_url, request_token = handshaker.initiate()
    session['request_token'] = request_token
    session['return_to_url'] = request.args.get('next', '/')
    return redirect(redirect_url)


@auth.route("/oauth-callback")
def oauth_callback():
    handshaker = Handshaker(
        "https://meta.wikimedia.org/w/index.php",
        oauth_token
    )
    access_token = handshaker.complete(session['request_token'], request.query_string)
    session['acces_token'] = access_token
    identity = handshaker.identify(access_token)
    wiki_uid = identity['sub']
    user = g.conn.session.query(User).filter(User.wiki_uid == wiki_uid).first()
    if user is None:
        user = User(username=identity['username'], wiki_uid=wiki_uid)
        g.conn.session.add(user)
        g.conn.session.commit()
    session['user_id'] = user.id
    return_to_url = session.get('return_to_url')
    del session['request_token']
    del session['return_to_url']
    return redirect(return_to_url)


@auth.route("/logout")
def logout():
    session.clear()
    return redirect("/")
