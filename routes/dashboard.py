from flask import Blueprint, render_template, current_app, session, redirect, url_for, flash, request, jsonify
from db_config import connect_db
import mysql.connector
import pickle
import re
import string
import pandas as pd
import nltk
from auth_utils import role_required
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route("/dashboard")
def dashboard():
    db_connection = connect_db(current_app)
    cursor = db_connection.cursor()

    try:
        # Menghitung total jumlah data di tabel data_sentiment
        cursor.execute("SELECT COUNT(*) FROM data_sentiment")
        total_data = cursor.fetchone()[0]

        # Menghitung jumlah kolom pada tabel data_sentiment
        cursor.execute("SHOW COLUMNS FROM data_sentiment")
        jumlah_kolom = len(cursor.fetchall())

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

        # Tentukan sentimen dominan
        dominant_sentiment = "Positif" if positive_count > negative_count else "Negatif" if negative_count > positive_count else "Positif" if positive_count > 0 else "Negatif"

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
        dominant_sentiment=dominant_sentiment,
    )

# Inisialisasi blueprint dan file pickle model serta vectorizer
model_path = 'static/models/sentiment_model.pkl'
vectorizer_path = 'static/models/tfidf_vectorizer.pkl'

with open(vectorizer_path, 'rb') as f:
    vectorizer = pickle.load(f)

with open(model_path, 'rb') as f:
    model = pickle.load(f)

# Fungsi Preprocessing
def preprocess_text(text):
    text = text.lower()
    text = re.sub(r'\d+', '', text)  # Hapus angka
    text = text.translate(str.maketrans('', '', string.punctuation))  # Hapus tanda baca
    stop_words = set(stopwords.words('indonesian'))
    words = text.split()
    words = [word for word in words if word not in stop_words]
    return ' '.join(words)

@dashboard_bp.route('/klasifikasi_realtime', methods=['GET', 'POST'])
def klasifikasi_realtime():
    db = connect_db(current_app)
    cursor = db.cursor()

    try:
        if request.method == 'POST':
                # Mengambil teks dari form (atau body JSON jika menggunakan AJAX)
                text = request.json.get('text')  # Jika menggunakan AJAX dan JSON

                if not text:
                    return jsonify({"error": "Tidak ada teks yang diberikan"}), 400

                # Proses teks dan klasifikasi
                cleaned_text = preprocess_text(text)
                text_vectorized = vectorizer.transform([cleaned_text])
                prediction = model.predict(text_vectorized)[0]

                # Mengembalikan hasil klasifikasi dan preprocessing dalam format JSON
                return jsonify({
                    "full_text": text,
                    "preprocessed_text": cleaned_text,
                    "sentiment": prediction
                })
            
        return render_template('dashboard.html')

    except mysql.connector.Error as err:
        return f"Error: {err}"
    finally:
        cursor.close()
        db.close()

@dashboard_bp.route('/add-record', methods=['GET', 'POST'])
@role_required('admin', 'super_admin')
def add_record():
    if request.method == 'POST':
        # Proses input data (misalnya simpan ke database)
        pass
    return render_template('add_record.html')
