from flask import Blueprint, render_template, current_app, session, redirect, url_for, flash, request, jsonify
from db_config import connect_db
import mysql.connector
from auth_utils import role_required

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route("/dashboard")
def dashboard():
    # Cek apakah user sudah login
    if "user_id" not in session:
        flash("Please log in to access the dashboard.", "warning")
        return redirect(url_for("login.login"))

    db_connection = connect_db(current_app)
    cursor = db_connection.cursor()

    try:
        # Menghitung total jumlah data di tabel data_sentiment
        cursor.execute("SELECT COUNT(*) FROM data_sentiment")
        total_data = cursor.fetchone()[0]  # Mengambil hasil dari query

        # Menghitung jumlah kolom pada tabel data_sentiment
        cursor.execute("SHOW COLUMNS FROM data_sentiment")
        jumlah_kolom = len(cursor.fetchall())  # Menghitung jumlah kolom

        # Mengambil hasil akurasi dari tabel data_training_hasil
        cursor.execute("SELECT training_accuracy_percent FROM data_training_hasil")
        training_accuracy = cursor.fetchone()
        training_accuracy_percent = training_accuracy[0] if training_accuracy else "N/A"

        # Mengambil hasil akurasi dari tabel data_testing_hasil
        cursor.execute("SELECT testing_accuracy_percent FROM data_testing_hasil")
        testing_accuracy = cursor.fetchone()
        testing_accuracy_percent = testing_accuracy[0] if testing_accuracy else "N/A"

        # Mengambil data testing untuk prediksi
        cursor.execute("SELECT label FROM data_testing")
        rows = cursor.fetchall()

        if not rows:
            return jsonify({"error": "No data available for testing."}), 400

        # Hitung jumlah kalimat positif, negatif, dan netral
        labels_list = [row[0] for row in rows]
        positive_count = labels_list.count("Positif")
        negative_count = labels_list.count("Negatif")
        neutral_count = labels_list.count("Netral")

        # Tentukan sentimen dominan (positif atau negatif) meskipun ada netral
        dominant_sentiment = None
        if positive_count > negative_count:
            dominant_sentiment = "Positif"
        elif negative_count > positive_count:
            dominant_sentiment = "Negatif"
        else:
            dominant_sentiment = "Positif" if positive_count > 0 else "Negatif"

    except mysql.connector.Error as err:
        total_data = "Error: " + str(err)
        jumlah_kolom = "Error: " + str(err)
        training_accuracy_percent = "Error"
        testing_accuracy_percent = "Error"
        dominant_sentiment = "Error"

    finally:
        cursor.close()
        db_connection.close()

    return render_template(
        "index.html",
        jumlah_data=total_data,
        jumlah_kolom=jumlah_kolom,
        training_accuracy_percent=training_accuracy_percent,
        testing_accuracy_percent=testing_accuracy_percent,
        dominant_sentiment=dominant_sentiment,  # Kirim nilai sentimen dominan
    )


@dashboard_bp.route('/add-record', methods=['GET', 'POST'])
@role_required('admin', 'super_admin')  # Hanya admin dan super admin yang bisa akses
def add_record():
    if request.method == 'POST':
        # Proses input data
        # Misalnya: title = request.form['title']
        pass
    return render_template('add_record.html')