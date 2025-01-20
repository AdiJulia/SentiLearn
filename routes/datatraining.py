from flask import (
    Blueprint,
    render_template,
    current_app,
    Blueprint,
)
import pandas as pd
import mysql.connector
from db_config import connect_db
import json

datatraining_bp = Blueprint("data_training", __name__)

# untuk menampilkan hasilnya di halaman utama
@datatraining_bp.route("/hal_data_training", methods=["GET", "POST"])
def hal_data_training():
    db = connect_db(current_app)
    cursor = db.cursor()

    try:
        # Jika metode adalah GET, ambil data untuk ditampilkan
        # Data Sentimen
        cursor.execute("SELECT username, label, text_stemmed FROM data_training")
        rows_sentimen = cursor.fetchall()

        # Hasil Training
        cursor.execute(
            "SELECT model_name, training_accuracy, training_accuracy_percent, precision_score, recall, f1_score, support FROM data_training_hasil"
        )
        rows_training = cursor.fetchall()

        # Membuat DataFrame dari data yang diambil
        data_sentimen = pd.DataFrame(
            rows_sentimen, columns=["username", "label", "text_stemmed"]
        )
        training_results = pd.DataFrame(
            rows_training,
            columns=[
                "model_name",
                "training_accuracy",
                "training_accuracy_percent",
                "precision_score",
                "recall",
                "f1_score",
                "support",
            ],
        )
        
        classification_report_table = []  # Default jika tidak ada data
        classification_report_columns = ["Class", "Precision", "Recall", "F1-Score", "Support"]

        # Jika ada hasil testing di database, ambil dan masukkan ke classification_report_table
        cursor.execute("SELECT classification_report FROM data_training_hasil WHERE model_name = 'Logistic Regression'")
        classification_report_json = cursor.fetchone()

        classification_report_table = []

        if classification_report_json:
            try:
                report_test = json.loads(classification_report_json[0])  # Parsing JSON dari database
                
                for label, metrics in report_test.items():
                    if isinstance(metrics, dict) and label not in ["accuracy", "macro avg", "weighted avg"]:  # Proses hanya data label
                        classification_report_table.append(
                            [
                                label,
                                round(metrics.get("precision", 0), 2),  # Ganti precision_score dengan precision
                                round(metrics.get("recall", 0), 2),  # Gunakan get untuk keamanan
                                round(metrics.get("f1-score", 0), 2),  # Gunakan get untuk keamanan
                                metrics.get("support", 0),  # Gunakan get untuk keamanan
                            ]
                        )
                
                # Tambahkan rata-rata weighted
                if "weighted avg" in report_test:
                    classification_report_table.append(
                        [
                            "Weighted Avg",
                            round(report_test["weighted avg"]["precision"], 2),
                            round(report_test["weighted avg"]["recall"], 2),
                            round(report_test["weighted avg"]["f1-score"], 2),
                            report_test["weighted avg"]["support"],
                        ]
                    )
            except json.JSONDecodeError:
                print("Error decoding JSON from classification report.")
            except Exception as e:
                print(f"An error occurred: {e}")
        else:
            print("No classification report found for the specified model.")
            
        return render_template(
            "data_training.html",
            data_sentimen=data_sentimen.values.tolist(),
            data_training=training_results.values.tolist(),
            jumlah_data_sentimen=len(data_sentimen),
            jumlah_data_training=len(training_results),
            classification_report_table=classification_report_table,
            classification_report_columns=classification_report_columns,
        )
    except mysql.connector.Error as err:
        return f"Error: {err}"
    finally:
        cursor.close()
        db.close()


@datatraining_bp.route("/reset_table_training", methods=["POST"])
def reset_table_training():
    db = connect_db(current_app)
    cursor = db.cursor()

    # Hapus semua data dari tabel
    cursor.execute(
        "TRUNCATE TABLE data_training_hasil"
    )  # Ini akan menghapus semua data dan mengatur ulang AUTO_INCREMENT
    cursor.execute("TRUNCATE TABLE data_training")
    db.commit()
    cursor.close()
    db.close()
    return render_template("data_training.html")
