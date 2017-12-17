from flask import Blueprint, request, session, redirect, g
from mwoauth import ConsumerToken, Handshaker
from .models.user import User
from requests import __version__ as requests_version
from socket import getfqdn
from sqlalchemy.exc import IntegrityError

auth = Blueprint('auth', __name__)

oauth_token = None
# User-agent used by mwoauth requests made during oauth handshake
user_agent = 'Quarry %s (https://wikitech.wikimedia.org/wiki/Nova_Resource:Quarry) Python-requests/%s' \
                    % (getfqdn(), requests_version)


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
        oauth_token,
        user_agent=user_agent
    )
    redirect_url, request_token = handshaker.initiate()
    session['request_token'] = request_token
    session['return_to_url'] = request.args.get('next', '/')
    return redirect(redirect_url)


@auth.route("/oauth-callback")
def oauth_callback():
    handshaker = Handshaker(
        "https://meta.wikimedia.org/w/index.php",
        oauth_token,
        user_agent=user_agent
    )
    access_token = handshaker.complete(session['request_token'], request.query_string)
    session['access_token'] = access_token
    identity = handshaker.identify(access_token)
    wiki_uid = identity['sub']
    user = g.conn.session.query(User).filter(User.wiki_uid == wiki_uid).first()
    if user is None:
        user = User(username=identity['username'], wiki_uid=wiki_uid)
        g.conn.session.add(user)
        g.conn.session.commit()
    elif user.username != identity['username']:
        user.username = identity['username']
        g.conn.session.add(user)
        try:
            g.conn.session.commit()
        except IntegrityError as e:
            if e[0] == 1062:  # Duplicate
                g.conn.session.rollback()
            else:
                raise

    session['user_id'] = user.id
    return_to_url = session.get('return_to_url')
    del session['request_token']
    del session['return_to_url']
    return redirect(return_to_url)


@auth.route("/logout")
def logout():
    session.clear()
    return redirect("/")
