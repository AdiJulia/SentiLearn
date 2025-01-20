from flask import Blueprint, render_template, current_app, request, redirect, render_template, flash, url_for
import pandas as pd
from db_config import connect_db
import mysql.connector
import chardet
from auth_utils import role_required

import_data_bp = Blueprint('import_data', __name__)

@import_data_bp.route('/import_data')
def import_data():
    db_connection = connect_db(current_app)
    cursor = db_connection.cursor()

    try:
        # Menghitung total jumlah data di tabel data_sentiment
        cursor.execute("SELECT COUNT(*) FROM data_sentiment")
        total_data = cursor.fetchone()[0]  # Mengambil hasil dari query
        
        # Menghitung jumlah kolom pada tabel data_sentiment
        cursor.execute("SHOW COLUMNS FROM data_sentiment")
        jumlah_kolom = len(cursor.fetchall())  # Menghitung jumlah kolom

    except mysql.connector.Error as err:
        total_data = "Error: " + str(err)
        jumlah_kolom = "Error: " + str(err)

    finally:
        cursor.close()
        db_connection.close()

    return render_template('import.html', jumlah_data=total_data, jumlah_kolom=jumlah_kolom)

@import_data_bp.route('/import_csv', methods=['POST'])
def import_csv():
    db = connect_db(current_app)
    cursor = db.cursor()

    if 'csv_file' not in request.files:
        flash("No file part", "error") 
        return redirect(url_for('import_data.import_data'))

    file = request.files['csv_file']
    if file.filename == '':
        flash("No selected file", "error") 
        return redirect(url_for('import_data.import_data'))

    if file:
        try:
            raw_data = file.read()
            result = chardet.detect(raw_data)  
            detected_encoding = result['encoding'] 

            # Baca file CSV dengan encoding yang terdeteksi
            file.seek(0)  
            data = pd.read_csv(
                file,
                sep=';',  
                usecols=['full_text', 'username', 'label'],  
                skip_blank_lines=True,
                on_bad_lines='skip',
                encoding=detected_encoding
            )

            # Menghapus spasi di sekitar nama kolom
            data.columns = data.columns.str.strip()

            # Memastikan kolom yang diperlukan ada
            required_columns = ['full_text', 'username', 'label']
            if not all(col in data.columns for col in required_columns):
                flash("CSV file is missing required columns", "error")
                return redirect(url_for('import_data.import_data'))

            for _, row in data.iterrows():
                sql = "INSERT INTO data_sentiment (full_text, username, label) VALUES (%s, %s, %s)"
                cursor.execute(sql, (row['full_text'], row['username'], row['label']))

            db.commit()
            cursor.close()
            db.close()

            flash("File imported successfully", "success")  
            return redirect(url_for('import_data.import_data'))

        except ValueError as e:
            flash(f"ValueError: {e}", "error")
            return redirect(url_for('import_data.import_data'))
        except pd.errors.ParserError as e:
            flash(f"ParserError: {e}", "error")
            return redirect(url_for('import_data.import_data'))

    flash("File import failed", "error")  
    return redirect(url_for('import_data.import_data'))




@import_data_bp.route('/show_data', methods=['GET'])
def show_data():
    db = connect_db(current_app)  
    cursor = db.cursor()

    try:
        # Menghitung jumlah username unik
        cursor.execute("SELECT COUNT(DISTINCT username) FROM data_sentiment")
        total_items = cursor.fetchone()[0]  

        # Ambil semua data tanpa paginasi
        cursor.execute("SELECT full_text, username, label FROM data_sentiment")
        data = cursor.fetchall()  

        # Kolom yang akan ditampilkan
        columns = ['full_text', 'username', 'label']
        
        # Render template dengan data dari MySQL dan jumlah data
        return render_template('import.html', data=data, columns=columns, jumlah_data=len(data))

    except mysql.connector.Error as err:
        flash("No selected file", "error")
        return f"Error: {err}"
    finally:
        cursor.close()
        db.close()  
           
@import_data_bp.route('/reset_table_import', methods=['POST'])
def reset_table_import():
    db = connect_db(current_app)
    cursor = db.cursor()
    
    cursor.execute("TRUNCATE TABLE data_sentiment")  

    db.commit()
    cursor.close()
    db.close()
    return render_template('import.html')