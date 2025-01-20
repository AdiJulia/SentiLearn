from flask import Blueprint, render_template, current_app
import pandas as pd
import mysql.connector
from db_config import connect_db
import json

datatesting_bp = Blueprint("data_testing", __name__)


@datatesting_bp.route("/hal_data_testing", methods=["GET", "POST"])
def hal_data_testing():
    db = connect_db(current_app)
    cursor = db.cursor()

    try:
        # Data Sentimen
        cursor.execute(
            "SELECT username, label, text_stemmed FROM data_testing"
        )
        rows_sentimen = cursor.fetchall()  # Pastikan hasil query pertama dikonsumsi

        # Hasil Testing
        cursor.execute(
            "SELECT model_name, testing_accuracy, testing_accuracy_percent, precision_score, recall, f1_score, support FROM data_testing_hasil"
        )
        rows_testing = cursor.fetchall()  # Pastikan hasil query pertama dikonsumsi
        # Ensure you handle the rows properly before using them in a DataFrame

        # Membuat DataFrame dari data yang diambil untuk dikirim ke template
        data_sentimen = pd.DataFrame(
            rows_sentimen,
            columns=["username", "label", "text_stemmed"],
        )
        data_testing = pd.DataFrame(
            rows_testing,
            columns=[
                "model_name",
                "testing_accuracy",
                "testing_accuracy_percent",
                "precision_score",
                "recall",
                "f1_score",
                "support",
            ],
        )   

        classification_report_table = []  # Default jika tidak ada data
        classification_report_columns = ["Class", "Precision", "Recall", "F1-Score", "Support"]

        # Jika ada hasil testing di database, ambil dan masukkan ke classification_report_table
        cursor.execute("SELECT classification_report FROM data_testing_hasil WHERE model_name = 'Logistic Regression'")
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


        # Kirim ke template
        return render_template(
            "data_testing.html",
            data_sentimen=data_sentimen.values.tolist(),
            data_testing=data_testing.values.tolist(),
            jumlah_data_sentimen=len(data_sentimen),
            jumlah_data_testing=len(data_testing),
            classification_report_table=classification_report_table,
            classification_report_columns=classification_report_columns,
        )

    except mysql.connector.Error as err:
        return f"Error: {err}"
    finally:
        cursor.close()
        db.close()


@datatesting_bp.route("/reset_table_testing", methods=["POST"])
def reset_table_testing():
    db = connect_db(current_app)
    cursor = db.cursor()

    # Hapus semua data dari tabel
    cursor.execute(
        "TRUNCATE TABLE data_testing_hasil"
    )  # Ini akan menghapus semua data dan mengatur ulang AUTO_INCREMENT
    cursor.execute( 
        "TRUNCATE TABLE data_testing"
    )
    db.commit()
    cursor.close()
    db.close()
    return render_template("data_testing.html")
