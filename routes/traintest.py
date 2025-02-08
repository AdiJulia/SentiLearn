from flask import Blueprint, jsonify, current_app, request, url_for, redirect
import mysql.connector
import numpy as np
import json
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix
from db_config import connect_db
import os
import pickle


traintest_bp = Blueprint('train_test', __name__)

def check_data_exists(cursor):
    cursor.execute("SELECT COUNT(*) FROM data_training_hasil")
    training_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM data_testing_hasil")
    testing_count = cursor.fetchone()[0]
    return training_count > 0, testing_count > 0

@traintest_bp.route('/trainingtesting', methods=['POST'])
def trainingtesting():
    db = connect_db(current_app)
    cursor = db.cursor()

    try:
        # Mengambil parameter redirect_page dari form agar kembali ke form semulaa
        redirect_page = request.form.get('redirect_page')

        # Cek apakah data sudah ada di tabel
        training_exists, testing_exists = check_data_exists(cursor)

        if training_exists and testing_exists:
            return redirect(url_for(redirect_page))

        # Ambil data dari tabel data_extraction
        cursor.execute("SELECT label, text_extraction FROM data_extraction")
        rows = cursor.fetchall()

        if not rows:
            return jsonify({"error": "No data available for training."}), 400

        text_labeled, text_extraction = zip(*rows)

        X = []
        y = []
        invalid_data_count = 0

        for extraction, label in zip(text_extraction, text_labeled):
            if extraction and label:
                try:
                    extraction_values = list(map(float, extraction.split(',')))
                    X.append(extraction_values)
                    y.append(label)
                except Exception as e:
                    print(f"Error processing data: {e} for extraction: {extraction}")
                    invalid_data_count += 1
                    continue
            else:
                invalid_data_count += 1

        if len(X) != len(y):
            return jsonify({"error": "Mismatch in number of samples between features and labels."}), 400

        if len(X) == 0:
            return jsonify({"error": "No valid data available for training after cleaning invalid data."}), 400

        print(f"Valid data count: {len(X)}")
        print(f"Invalid data count: {invalid_data_count}")

        X = np.array(X)
        y = np.array(y)

        # Pisahkan data menjadi data training dan testing (80% training, 20% testing)
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Pelatihan model Logistic Regression
        logreg = LogisticRegression(penalty='l2', solver='liblinear', random_state=0, class_weight='balanced')
        # solver='liblinear' untuk pengoptimalan yang digunakan oleh Logistic Regression. random_state=0: Mengatur nilai acak untuk hasil yang konsisten.
        
        # Cek apakah model sudah ada
        model_path = 'static/models/sentiment_model.pkl'
        vectorizer_path = 'static/models/tfidf_vectorizer.pkl'

        if os.path.exists(model_path) and os.path.exists(vectorizer_path):
            return jsonify({"message": "Model sudah ada, tidak perlu training ulang."}), 200
        
        logreg.fit(X_train, y_train)

        # Mengukur akurasi pada training set
        score_train = logreg.score(X_train, y_train)
        report_train = classification_report(y_train, logreg.predict(X_train), output_dict=True)

        metrics_summary_train = {
            "precision": report_train['weighted avg']['precision'],
            "recall": report_train['weighted avg']['recall'],
            "f1_score": report_train['weighted avg']['f1-score'],
            "support": report_train['weighted avg']['support'],
        }

        # Menyimpan hasil ke tabel data_training_hasil
        model_name = 'Logistic Regression'
        classification_report_train_json = json.dumps(report_train)
        training_accuracy_percent = score_train * 100

        cursor.execute("""
            INSERT INTO data_training_hasil (`model_name`, `training_accuracy`, `training_accuracy_percent`, `classification_report`, `precision_score`, `recall`, `f1_score`, `support`)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            model_name,
            score_train,
            training_accuracy_percent,
            classification_report_train_json,
            metrics_summary_train["precision"],
            metrics_summary_train["recall"],
            metrics_summary_train["f1_score"],
            metrics_summary_train["support"],
        ))
        db.commit()

        # Evaluasi model pada data testing
        score_test = logreg.score(X_test, y_test)
        report_test = classification_report(y_test, logreg.predict(X_test), output_dict=True)

        metrics_summary_test = {
            "precision": report_test['weighted avg']['precision'],
            "recall": report_test['weighted avg']['recall'],
            "f1_score": report_test['weighted avg']['f1-score'],
            "support": report_test['weighted avg']['support'],
        }

        # Menyimpan hasil ke tabel data_testing_hasil
        classification_report_test_json = json.dumps(report_test)
        testing_accuracy_percent = score_test * 100

        cursor.execute("""
            INSERT INTO data_testing_hasil (`model_name`, `testing_accuracy`, `testing_accuracy_percent`, `classification_report`, `precision_score`, `recall`, `f1_score`, `support`)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            model_name,
            score_test,
            testing_accuracy_percent,
            classification_report_test_json,
            metrics_summary_test["precision"],
            metrics_summary_test["recall"],
            metrics_summary_test["f1_score"],
            metrics_summary_test["support"],
        ))
        db.commit()

        # Menghitung confusion matrix
        y_pred = logreg.predict(X_test)
        cm = confusion_matrix(y_test, y_pred)

        # Membuat heatmap untuk confusion matrix
        plt.figure(figsize=(8, 6))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=np.unique(y), yticklabels=np.unique(y))
        plt.ylabel('Actual Labels')
        plt.xlabel('Predicted Labels')
        plt.title('Confusion Matrix')

        cm_image_path = os.path.join(current_app.static_folder, 'images', 'confusion_matrix.png')
        plt.savefig(cm_image_path)
        plt.close()
        
        with open('static/models/sentiment_model.pkl', 'wb') as f:
            pickle.dump(logreg, f)

        return redirect(url_for(redirect_page))

    except mysql.connector.Error as err:
        return jsonify({"error": f"Database error: {err}"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        db.close()