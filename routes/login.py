from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from werkzeug.security import check_password_hash
from db_config import connect_db  # Koneksi ke database

login_bp = Blueprint('login', __name__)

@login_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email_username = request.form['email-username']
        password = request.form['password']

        db_connection = connect_db(current_app)
        cursor = db_connection.cursor(dictionary=True)

        try:
            query = "SELECT * FROM users WHERE email = %s OR username = %s"
            cursor.execute(query, (email_username, email_username))
            user = cursor.fetchone()

            if user and check_password_hash(user['password'], password):
                session['user_id'] = user['id']
                session['role'] = user['role']
                session['username'] = user['username']

                flash('Login successful!', 'success')

                # Redirect berdasarkan role
                return redirect(url_for('dashboard.dashboard'))

            flash('Invalid email/username or password.', 'error')
        except Exception as e:
            flash(f"An error occurred: {str(e)}", 'error')
        finally:
            cursor.close()
            db_connection.close()

    return render_template('auth/login.html')

@login_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login.login'))
