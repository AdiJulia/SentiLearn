import mysql.connector
from flask import current_app, Flask

def connect_db(app: Flask):
    try:
        connection = mysql.connector.connect(
            host=app.config['MYSQL_HOST'],
            user=app.config['MYSQL_USER'],
            password=app.config['MYSQL_PASSWORD'],
            database=app.config['MYSQL_DB'],
            connect_timeout=600
        )
        return connection
    except mysql.connector.Error as err:
        print(f"Error connecting to MySQL: {err}")
        return None  # Pastikan Anda menangani koneksi gagal di aplikasi
