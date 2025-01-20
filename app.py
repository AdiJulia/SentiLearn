from flask import Flask, render_template
import os
from routes import register_blueprints
from dotenv import load_dotenv
from auth_utils import role_required

app = Flask(__name__)
register_blueprints(app)
app.secret_key = os.urandom(24)

application = app

load_dotenv()

# Konfigurasi MySQL 
app.config['MYSQL_HOST'] = 'localhost'  # Nama service pada docker-compose
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root123'
app.config['MYSQL_DB'] = 'sentilearn'

app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

@app.route('/')
def index():
    return render_template('login.html')
    # return render_template('index.html')

# # Rute untuk role `user`
# @app.route('/view-only')
# @role_required('user', 'admin', 'super_admin')
# def view_only():
#     return "This is a view-only page. No interactions allowed."

# # Rute untuk role `admin` (tanpa akses ke manajemen pengguna)
# @app.route('/admin-page')
# @role_required('admin', 'super_admin')
# def admin_page():
#     return "Admin can manage content but not users."

# # Rute untuk role `super_admin`
# @app.route('/manage-users')
# @role_required('super_admin')
# def manage_users():
#     return "Super Admin can manage users and everything else."

if __name__ == '__main__':
    app.run(debug=True, threaded=True, port=30000)
