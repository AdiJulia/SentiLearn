from sklearn.feature_extraction.text import TfidfVectorizer
from flask import Blueprint, current_app, render_template, request, url_for, redirect
import pandas as pd
import mysql.connector
import matplotlib
import pickle
from db_config import connect_db
from sklearn.model_selection import train_test_split
matplotlib.use('Agg')

feature_extraction_bp = Blueprint('feature_extraction', __name__)

@feature_extraction_bp.route('/hal_feature_extraction', methods=['GET', 'POST'])
def hal_feature_extraction():
    db = connect_db(current_app)
    cursor = db.cursor()

    try:
        if request.method == 'POST':
            feature_extraction()
            return redirect(url_for('feature_extraction.hal_feature_extraction'))
        
        cursor.execute("SELECT username, label, text_stemmed, text_extraction FROM data_extraction")
        rows = cursor.fetchall()
        data = pd.DataFrame(rows, columns=['username', 'label', 'text_stemmed', 'text_extraction'])

        # Menghapus kolom text_extraction sebelum mengirim data ke template
        data = data.drop(columns=['text_extraction'])

        columns = data.columns.tolist()
        data_list = data.values.tolist()

        return render_template('feature_extraction.html', columns=columns, data=data_list, jumlah_data=len(data_list))

    except mysql.connector.Error as err:
        return f"Error: {err}"
    finally:
        cursor.close()
        db.close()
        
@feature_extraction_bp.route('/feature_extraction', methods=['POST'])
def feature_extraction():
    db = connect_db(current_app)
    cursor = db.cursor()

    try:
        # Mengambil data dari tabel data_preprocessing
        cursor.execute("SELECT username, label, full_text, text_stemmed FROM data_preprocessing")
        rows = cursor.fetchall()

        if not rows:
            return "No data available for TF-IDF extraction."

        # Memisahkan data ke dalam list
        username_list, label_list, full_text_list, text_stemmed_list = zip(*rows)

        # Inisialisasi TF-IDF Vectorizer
        vectorizer = TfidfVectorizer()

        # Melakukan transformasi TF-IDF
        tfidf_matrix = vectorizer.fit_transform(text_stemmed_list)
        tfidf_features = vectorizer.get_feature_names_out()

        # Menyimpan hasil TF-IDF ke dalam tabel data_extraction
        insert_query = """
        INSERT INTO data_extraction (username, label, full_text, text_stemmed, text_extraction)
        VALUES (%s, %s, %s, %s, %s)
        """
        for i, row in enumerate(tfidf_matrix.toarray()):
            # Konversi vektor TF-IDF menjadi string yang dipisahkan koma
            text_extraction = ','.join(map(str, row))  
            cursor.execute(insert_query, (
                username_list[i],
                label_list[i],
                full_text_list[i],
                text_stemmed_list[i],
                text_extraction
            ))

        db.commit()
        
        # Simpan vectorizer ke dalam file pickle
        vectorizer_path = 'static/models/tfidf_vectorizer.pkl'
        with open(vectorizer_path, 'wb') as f:
            pickle.dump(vectorizer, f)
            
        return "TF-IDF successfully extracted and stored in data_extraction."

    except mysql.connector.Error as err:
        return f"Error: {err}"

    finally:
        cursor.close()
        db.close()
        
@feature_extraction_bp.route('/split_data', methods=['POST'])
def split_data_route():
    result = split_data_proses()
    return redirect(url_for('feature_extraction.hal_feature_extraction', message=result))

@feature_extraction_bp.route('/split_data_proses', methods=['POST'])
def split_data_proses():
    db = connect_db(current_app)
    cursor = db.cursor()
    try:
        # Mengambil data dari tabel data_extraction
        cursor.execute("SELECT username, label, full_text, text_stemmed, text_extraction FROM data_extraction")
        rows = cursor.fetchall()

        if not rows:
            return "No data available for splitting."

        # Membuat DataFrame
        data = pd.DataFrame(rows, columns=['username', 'label', 'full_text', 'text_stemmed', 'text_extraction'])

        # Melakukan split data
        train_data, test_data = train_test_split(data, test_size=0.2, random_state=42)

        cursor.execute("DELETE FROM data_training")
        cursor.execute("DELETE FROM data_testing")

        # Menyimpan data training ke tabel data_training
        for _, row in train_data.iterrows():
            sql_train = """
                INSERT INTO data_training (username, label, full_text, text_stemmed, text_extraction)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(sql_train, (row['username'], row['label'], row['full_text'], row['text_stemmed'], row['text_extraction']))

        # Menyimpan data testing ke tabel data_testing
        for _, row in test_data.iterrows():
            sql_test = """
                INSERT INTO data_testing (username, label, full_text, text_stemmed, text_extraction)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(sql_test, (row['username'], row['label'], row['full_text'], row['text_stemmed'], row['text_extraction']))

        db.commit()
        return "Data successfully split into training and testing sets."
    


    except mysql.connector.Error as err:
        return f"Error: {err}"
    finally:
        cursor.close()
        db.close()

@feature_extraction_bp.route('/reset_table_extraction', methods=['POST'])
def reset_table_extraction():
    db = connect_db(current_app)
    cursor = db.cursor()
    
    cursor.execute("TRUNCATE TABLE data_extraction") 

    db.commit()
    cursor.close()
    db.close()
    return render_template('feature_extraction.html')