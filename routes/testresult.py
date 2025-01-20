from flask import Blueprint, render_template, request, jsonify, current_app
from wordcloud import WordCloud, STOPWORDS
import mysql.connector
from db_config import connect_db
import os

testresult_bp = Blueprint("test_result", __name__)


@testresult_bp.route("/hal_test_result", methods=["POST", "GET"])
def hal_test_result():
    if request.method == "POST":
        return testresult()  

    return render_template("test_result.html") 


@testresult_bp.route("/testresult", methods=["POST", "GET"])
def testresult():
    db = connect_db(current_app)
    cursor = db.cursor()

    try:
        # Fetch model and testing data
        cursor.execute(
            "SELECT model_name, training_accuracy, training_accuracy_percent, precision_score, recall, f1_score, support FROM data_training_hasil"
        )
        data_training = cursor.fetchall()

        cursor.execute(
            """
            SELECT model_name, testing_accuracy, testing_accuracy_percent, precision_score, recall, f1_score, support 
            FROM data_testing_hasil
        """
        )
        data_testing = cursor.fetchall()

        # Ambil data testing untuk prediksi
        cursor.execute("SELECT label, text_stemmed, text_extraction FROM data_testing")
        rows = cursor.fetchall()

        if not rows:
            return jsonify({"error": "No data available for testing."}), 400

        labels_list, text_stemmed_list, text_extraction_list = zip(*rows)

        # Hitung jumlah kalimat positif, negatif, dan netral
        positive_count = labels_list.count("Positif")
        negative_count = labels_list.count("Negatif")
        neutral_count = labels_list.count("Netral")

        summary_data = [
            {"Label": "Positif", "Count": positive_count},
            {"Label": "Negatif", "Count": negative_count},
            {"Label": "Netral", "Count": neutral_count},
        ]

        # Mengonversi text_extraction menjadi array
        X = []
        for extraction in text_extraction_list:
            try:
                extraction_values = extraction.strip().split(",")
                X.append([float(x) for x in extraction_values])
            except ValueError as e:
                return jsonify({"error": f"Error parsing text_extraction: {e}"}), 400

        # Pisahkan teks berdasarkan label (positif dan negatif)
        positive_texts = [
            text_stemmed_list[i]
            for i in range(len(labels_list))
            if labels_list[i] == "Positif"
        ]
        negative_texts = [
            text_stemmed_list[i]
            for i in range(len(labels_list))
            if labels_list[i] == "Negatif"
        ]

        # Gabungkan teks menjadi satu string
        positive_text = " ".join(positive_texts) if positive_texts else ""
        negative_text = " ".join(negative_texts) if negative_texts else ""

        # Jika teks positif atau negatif kosong, kirim error
        if not positive_text and not negative_text:
            return (
                jsonify(
                    {
                        "error": "Tidak ada teks positif atau negatif yang tersedia untuk membuat WordCloud."
                    }
                ),
                400,
            )

        # Stopwords untuk menghapus kata umum
        stopwords = STOPWORDS

        # Tentukan path untuk menyimpan gambar WordCloud
        positive_wc_path = os.path.join(
            current_app.static_folder, "images", "positive_wordcloud.png"
        )
        negative_wc_path = os.path.join(
            current_app.static_folder, "images", "negative_wordcloud.png"
        )

        # Membuat WordCloud untuk teks positif
        wc_positive = WordCloud(
            background_color="white",
            stopwords=stopwords,
            height=600,
            width=800,
            max_words=100,
            colormap="viridis",
        ).generate(positive_text)

        # Simpan WordCloud positif ke file
        wc_positive.to_file(positive_wc_path)

        # Membuat WordCloud untuk teks negatif
        wc_negative = WordCloud(
            background_color="white",
            stopwords=stopwords,
            height=600,
            width=800,
            max_words=100,
            colormap="plasma",
        ).generate(negative_text)

        # Simpan WordCloud negatif ke file
        wc_negative.to_file(negative_wc_path)

        # Render hasil di halaman test_result.html dengan WordCloud dan gambar confusion matrix
        return render_template(
            "test_result.html",
            data_training=data_training,
            data_testing=data_testing,
            summary_data=summary_data,
            confusion_matrix_img="images/confusion_matrix.png",  # Kirim path gambar confusion matrix ke template
            positive_wordcloud_img="images/positive_wordcloud.png",  # Kirim image WordCloud positif ke template
            negative_wordcloud_img="images/negative_wordcloud.png",  # Kirim image WordCloud negatif ke template
        )

    except mysql.connector.Error as err:
        return jsonify({"error": f"Database error: {err}"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        db.close()