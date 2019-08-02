from functools import wraps
from flask import flash, redirect, url_for, session, abort


# Wrappers for sessions
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Not logged in', 'danger')
            return redirect(url_for('index'))
    return wrap


def is_logged_out(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' not in session:
            return f(*args, **kwargs)
        else:
            return redirect(url_for('index'))
    return wrap


# Determines if they're a moderator
def is_moderator(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged in' in session:
            if 'access_level' in session > 0:
                return f(*args, **kwargs)
        abort(404)
    return wrap


# Determines if they're a moderator
def is_admin(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            if 'access_level' in session == 2:
                return f(*args, **kwargs)
        abort(404)
    return wrap
