from flask import session, redirect, url_for, flash, request
from functools import wraps

def role_required(*roles):
    """
    Middleware untuk memeriksa apakah pengguna memiliki salah satu peran yang diizinkan.
    """
    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            if 'role' not in session:
                flash('You need to log in first.', 'error')
                return redirect(url_for('login.login'))
            
            if session['role'] not in roles:
                flash('You do not have permission to access this page.', 'error')
                return redirect(request.referrer or url_for('dashboard.dashboard'))
            
            return fn(*args, **kwargs)
        return decorated_view
    return wrapper
