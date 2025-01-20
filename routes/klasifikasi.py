from flask import Blueprint, request, redirect, render_template, url_for, current_app
import pandas as pd
import mysql.connector
from db_config import connect_db

klasifikasi_bp = Blueprint('klasifikasi', __name__)

# Membaca file TSV untuk kamus positif dan negatif
positive_lexicon = set(pd.read_csv("routes/InSet-master/positive.tsv", sep="\t", header=None)[0])
negative_lexicon = set(pd.read_csv("routes/InSet-master/negative.tsv", sep="\t", header=None)[0])

def determine_sentiment(text):
    # Tokenisasi teks
    words = text.split()
    
    # Hitung jumlah kata positif dan negatif
    positive_count = sum(1 for word in words if word in positive_lexicon)
    negative_count = sum(1 for word in words if word in negative_lexicon)
    
    # Tentukan sentimen berdasarkan perbandingan kata positif dan negatif
    if positive_count > negative_count:
        return "Positive"
    elif positive_count < negative_count:
        return "Negative"
    else:
        return "Neutral"


@klasifikasi_bp.route('/hal_klasifikasi_data', methods=['GET', 'POST'])
def hal_klasifikasi_data():
    db = connect_db(current_app)
    cursor = db.cursor()

    try:
        # Jika metode adalah POST, lakukan klasifikasi
        if request.method == 'POST':
            # Jalankan proses klasifikasi data
            return klasifikasi_data()

        # Jika metode adalah GET, ambil data untuk ditampilkan
        cursor.execute("SELECT created_at, username, text_stemmed, text_labeled FROM data_labeling")
        rows = cursor.fetchall()

        # Membuat DataFrame dari data yang diambil untuk dikirim ke template
        data = pd.DataFrame(rows, columns=['created_at', 'username', 'text_stemmed', 'text_labeled'])
        columns = data.columns.tolist()
        data_list = data.values.tolist()

        return render_template('klasifikasi_data.html', columns=columns, data=data_list, jumlah_data=len(data_list))

    except mysql.connector.Error as err:
        return f"Error: {err}"
    finally:
        cursor.close()
        db.close()
        
@klasifikasi_bp.route('/klasifikasi_data', methods=['POST'])
def klasifikasi_data():
    db = connect_db(current_app)
    cursor = db.cursor()

    try:
        # Ambil data hasil preprocessing dari tabel data_preprocessing
        cursor.execute("SELECT created_at, username, text_stemmed FROM data_preprocessing")
        rows = cursor.fetchall()

        if not rows:
            return "No data available for labeling."

        # Konversi data menjadi DataFrame
        data = pd.DataFrame(rows, columns=['created_at', 'username', 'text_stemmed'])

        # Proses penentuan sentimen menggunakan kamus
        data['text_labeled'] = data['text_stemmed'].apply(determine_sentiment)

        # Simpan hasil labeling ke tabel data_labeling
        for _, row in data.iterrows():
            # Cek apakah data sudah ada di tabel data_labeling
            cursor.execute("SELECT COUNT(*) FROM data_labeling WHERE created_at = %s AND username = %s",
                           (row['created_at'], row['username']))
            exists = cursor.fetchone()[0]

            # Hanya simpan jika data belum ada
            if exists == 0:
                sql = "INSERT INTO data_labeling (created_at, username, text_stemmed, text_labeled) VALUES (%s, %s, %s, %s)"
                cursor.execute(sql, (row['created_at'], row['username'], row['text_stemmed'], row['text_labeled']))

        db.commit()

        # Redirect ke halaman klasifikasi data setelah klasifikasi selesai
        return redirect(url_for('klasifikasi.hal_klasifikasi_data'))

    except mysql.connector.Error as err:
        return f"Error: {err}"
    finally:
        cursor.close()
        db.close()


# @klasifikasi_bp.route('/klasifikasi_data', methods=['POST'])
# def klasifikasi_data():
#     db = connect_db(current_app)
#     cursor = db.cursor()

#     try:
#         # Load IndoBERT pre-trained model for sentiment classification
#         model_name = "indobenchmark/indobert-base-p1"
#         tokenizer = AutoTokenizer.from_pretrained(model_name)
#         model = AutoModelForSequenceClassification.from_pretrained(model_name)

#         # Ambil data hasil preprocessing dari tabel data_preprocessing
#         cursor.execute("SELECT created_at, username, text_stemmed FROM data_preprocessing")
#         rows = cursor.fetchall()

#         if not rows:
#             return "No data available for labeling."

#         # Konversi data menjadi DataFrame
#         data = pd.DataFrame(rows, columns=['created_at', 'username', 'text_stemmed'])
#         texts = data["text_stemmed"].tolist()  # Ambil kolom teks yang akan dianalisis

#         # Tokenisasi data dalam batch
#         batch_size = 32
#         label_results = []  # Inisialisasi hasil label

#         for i in range(0, len(texts), batch_size):
#             batch_texts = texts[i:i + batch_size]

#             # Tokenisasi data batch
#             inputs = tokenizer(batch_texts, padding=True, truncation=True, return_tensors="pt")

#             # Nonaktifkan gradien untuk inference
#             with torch.no_grad():
#                 outputs = model(**inputs)
#                 logits = outputs.logits

#             # Mendapatkan label prediksi
#             predicted_labels = torch.argmax(logits, dim=1)

#             # Mapping hasil prediksi ke label baru
#             for label in predicted_labels:
#                 if label.item() in [0, 4]:  # Negatif dan sangat negatif
#                     label_results.append("negatif")
#                 elif label.item() == 1:  # Netral
#                     label_results.append("netral")
#                 elif label.item() in [2, 3]:  # Positif dan sangat positif
#                     label_results.append("positif")

#         # Pastikan panjang label_results sama dengan jumlah teks
#         if len(label_results) != len(texts):
#             return f"Length mismatch: label_results ({len(label_results)}) != texts ({len(texts)})"

#         # Simpan hasil labeling ke tabel data_labeling
#         for index, row in data.iterrows():
#             cursor.execute("SELECT COUNT(*) FROM data_labeling WHERE created_at = %s AND username = %s",
#                            (row['created_at'], row['username']))
#             exists = cursor.fetchone()[0]

#             # Hanya simpan jika data belum ada
#             if exists == 0:
#                 sql = "INSERT INTO data_labeling (created_at, username, text_stemmed, text_labeled) VALUES (%s, %s, %s, %s)"
#                 cursor.execute(sql, (row['created_at'], row['username'], row['text_stemmed'], label_results[index]))  

#         db.commit()

#         # Redirect ke halaman klasifikasi data setelah klasifikasi selesai
#         return redirect(url_for('klasifikasi.hal_klasifikasi_data'))

#     except mysql.connector.Error as err:
#         return f"Error: {err}"
#     finally:
#         cursor.close()
#         db.close()

        
@klasifikasi_bp.route('/reset_table_klasifikasi', methods=['POST'])
def reset_table_klasifikasi():
    db = connect_db(current_app)
    cursor = db.cursor()
    
    # Hapus semua data dari tabel
    cursor.execute("TRUNCATE TABLE data_labeling")  # Ini akan menghapus semua data dan mengatur ulang AUTO_INCREMENT

    db.commit()
    cursor.close()
    db.close()
    return render_template('klasifikasi_data.html')