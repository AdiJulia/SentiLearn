from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from werkzeug.security import generate_password_hash
from db_config import connect_db
import mysql.connector

register_bp = Blueprint('register', __name__)

@register_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Ambil data dari form
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        terms = request.form.get('terms')

        # Validasi data input
        if not username or not email or not password:
            flash("All fields are required!", "error")
            return render_template('auth/register.html')
        
        if not terms:
            flash("You must agree to the terms and conditions.", "error")
            return render_template('auth/register.html')

        # Hash password
        hashed_password = generate_password_hash(password)

        # Simpan ke database
        db_connection = connect_db(current_app)
        cursor = db_connection.cursor(dictionary=True)

        try:
            # Periksa apakah email atau username sudah digunakan
            check_query = "SELECT * FROM users WHERE email = %s OR username = %s"
            cursor.execute(check_query, (email, username))
            existing_user = cursor.fetchone()

            if existing_user:
                flash("Email or username already exists. Please choose another one.", "error")
                return render_template('auth/register.html')

            # Tambahkan user ke database
            insert_query = """
                INSERT INTO users (username, email, password, role) 
                VALUES (%s, %s, %s, 'user')
            """
            cursor.execute(insert_query, (username, email, hashed_password))
            db_connection.commit()

            flash("Registration successful! Please log in.", "success")
            return redirect(url_for('login.login'))

        except mysql.connector.Error as err:
            flash(f"An error occurred: {err}", "error")
        finally:
            cursor.close()
            db_connection.close()

    return render_template('auth/register.html')
