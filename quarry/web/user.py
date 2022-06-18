from flask import Blueprint, session, redirect, g, render_template
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import joinedload
from sqlalchemy import desc, func
from .models.user import User, UserGroup
from .models.star import Star
from .models.query import Query

user_blueprint = Blueprint('user', __name__)


def get_user():
    if 'user_id' in session:
        if not hasattr(g, '_user'):
            session.permanent = True
            g._user = g.conn.session.query(User).filter(User.id == session['user_id']).one()
        return g._user
    return None


def get_preferences():
    if 'preferences' not in session:
        session['preferences'] = {}
    return session['preferences']


@user_blueprint.route("/sudo/<string:username>")
def sudo(username):
    user = get_user()
    if user is None:
        return 'Authorization required', 403
    if g.conn.session.query(UserGroup).filter(UserGroup.user_id == user.id)\
            .filter(UserGroup.group_name == 'sudo').first() is not None:
        new_user = g.conn.session.query(User).filter(User.username == username).first()
        session['user_id'] = new_user.id
        return redirect('/')
    else:
        return 'You do not have the sudo right', 403


@user_blueprint.route('/<user_name>')
def user_page(user_name):
    # Munge the user_name, and hope
    user_name = user_name.replace('_', ' ').lower()
    try:
        user = g.conn.session.query(User).filter(func.lower(User.username) == user_name).one()
    except NoResultFound:
        return render_template("404.html", message="User not found", user=get_user()), 404
    stats = {
        'query_count': g.conn.session.query(func.count(Query.id)).filter(Query.user_id == user.id).scalar(),
        'stars_count': g.conn.session.query(func.count(Star.id)).filter(Star.user_id == user.id).scalar()
    }
    draft_queries = g.conn.session.query(Query) \
        .filter(Query.user_id == user.id) \
        .filter_by(published=False) \
        .order_by(desc(Query.last_touched))
    published_queries = g.conn.session.query(Query)\
        .filter(Query.user_id == user.id)\
        .filter_by(published=True)\
        .order_by(desc(Query.last_touched))
    stars = g.conn.session.query(Star).join(Star.query) \
        .options(joinedload(Star.query))\
        .filter(Star.user_id == user.id) \
        .order_by(desc(Star.timestamp))
    return render_template(
        "user.html",
        display_user=user,
        user=get_user(),
        stats=stats,
        draft_queries=draft_queries,
        published_queries=published_queries,
        stars=stars,
        jsvars={'preferences': get_preferences() if get_user() else {}}
    )
