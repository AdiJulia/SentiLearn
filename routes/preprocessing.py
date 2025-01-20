from flask import Blueprint, request, render_template, current_app, session, abort
import pandas as pd
import mysql.connector
import re
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from db_config import connect_db
nltk.download('punkt')
nltk.download('punkt_tab')
nltk.download('stopwords')

preprocessing_bp = Blueprint('preprocessing', __name__)

@preprocessing_bp.route('/hal_preprocessing', methods=['GET', 'POST'])
def hal_preprocessing():
    db = connect_db(current_app)
    cursor = db.cursor()
    
    try:
        if request.method == 'POST':
            user_role = session.get('user_role')
            if user_role not in ['admin', 'super_admin']:
                abort(403)  
            preprocessing()  
            
        
        cursor.execute("SELECT username, label, full_text, text_stemmed FROM data_preprocessing")
        rows = cursor.fetchall()

        # Membuat DataFrame dari data yang diambil untuk dikirim ke template
        data = pd.DataFrame(rows, columns=['username', 'label', 'full_text','text_stemmed'])
        columns = data.columns.tolist()
        data_list = data.values.tolist()

        return render_template('preprocessing_data.html', columns=columns, data=data_list, jumlah_data=len(data_list))

    except mysql.connector.Error as err:
        return f"Error: {err}"
    finally:
        cursor.close()
        db.close()

@preprocessing_bp.route('/preprocessing')
def preprocessing():
    db = connect_db(current_app)
    cursor = db.cursor()

    try:
        # Ambil data dari tabel data_sentiment
        cursor.execute("SELECT username, full_text, label FROM data_sentiment")
        rows = cursor.fetchall()

        # Membuat DataFrame dari data yang diambil
        data = pd.DataFrame(rows, columns=['username', 'full_text', 'label'])

        # 1. Handling missing value
        data = data.dropna()

        # 2. Cek duplikasi data
        data = data.drop_duplicates()

        # 3. Casefolding
        data['full_text'] = data['full_text'].str.lower()

        # 4. Cleansing
        def clean_text(tweet):
            tweet = re.sub(r'http\S+|www\.\S+', '', tweet)  # Menghapus URL
            tweet = re.sub(r'<.*?>', '', tweet)  # Menghapus HTML tags
            tweet = re.sub(r'@\S+', '', tweet)  # Menghapus mention
            tweet = re.sub(r'['
                        u'\U0001F600-\U0001F64F'
                        u'\U0001F300-\U0001F5FF'
                        u'\U0001F680-\U0001F6FF'
                        u'\U0001F1E0-\U0001F1FF'
                        ']+', '', tweet)  # Menghapus emoji
            tweet = re.sub(r'\d+', '', tweet)  # Menghapus angka
            tweet = re.sub(r'[^a-zA-Z\s]', '', tweet)  # Menghapus simbol dan tanda baca, kecuali spasi
            return tweet

        data['text_cleaned'] = data['full_text'].apply(clean_text)

        # 5. Normalisasi
        kamus_path = "static/kamus/kamus_kata_alay.xlsx"
        slang_word = pd.read_excel(kamus_path)

        # Membuat dictionary untuk kata slang
        slang_word_dict = {row[0]: row[1] for _, row in slang_word.iterrows()}

        def normalize_text(text):
            """
            Mengganti kata-kata slang dalam teks dengan kata standar sesuai kamus.
            """
            text = text.split()  # Tokenisasi sederhana dengan spasi
            text = [slang_word_dict[term] if term in slang_word_dict else term for term in text]
            return ' '.join(text)  # menggabungkan kembali menjadi string

        data['text_normalized'] = data['text_cleaned'].apply(normalize_text)

        # 6. Tokenizing
        nltk.download('punkt') 
        data['text_tokenized'] = data['text_normalized'].apply(word_tokenize)

        # 7. Stopwords removal
        nltk.download('stopwords') 
        stop_words = set(stopwords.words('indonesian'))

        def remove_stopwords(text):
            return [word for word in text if word not in stop_words]

        data['text_filtered'] = data['text_tokenized'].apply(remove_stopwords)

        # 8. Stemming
        # untuk mengubah kata ke bentuk dasar, e.g. (berlarian = lari)
        factory = StemmerFactory()
        stemmer = factory.create_stemmer()

        def stem_text(text):
            return [stemmer.stem(word) for word in text]

        data['text_stemmed'] = data['text_filtered'].apply(stem_text)

        # Menggabungkan kembali kata-kata hasil stemming menjadi kalimat
        data['text_stemmed'] = data['text_stemmed'].apply(lambda x: ' '.join(x))

        # 9. Hapus data sebelumnya di tabel data_preprocessing
        cursor.execute("DELETE FROM data_preprocessing")

        # 10. Simpan hasil preprocessing ke tabel data_preprocessing
        for _, row in data.iterrows():
            sql = "INSERT INTO data_preprocessing (username, label, full_text, text_stemmed) VALUES (%s, %s, %s, %s)"
            cursor.execute(sql, (row['username'], row['label'], row['full_text'], row['text_stemmed']))

        db.commit()
        return render_template('preprocessing_data.html')

    except mysql.connector.Error as err:
        return f"Error: {err}"
    finally:
        cursor.close()
        db.close()
        
@preprocessing_bp.route('/reset_table_preprocessing', methods=['POST'])
def reset_table_preprocessing():
    db = connect_db(current_app)
    cursor = db.cursor()
    
    cursor.execute("TRUNCATE TABLE data_preprocessing")

    db.commit()
    cursor.close()
    db.close()
    return render_template('preprocessing_data.html')
