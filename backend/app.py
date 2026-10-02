from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime

from routes.patient_routes import patient_routes
from services.prediction_service import prediction_service


# =========================================================
# FLASK APP
# =========================================================

app = Flask(__name__)

CORS(app)


# =========================================================
# REGISTER ROUTES
# =========================================================

app.register_blueprint(patient_routes)


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return jsonify({
        "status": "success",
        "message": "SAE Prediction System Backend is running"
    })


# =========================================================
# HEALTH
# =========================================================

@app.route("/api/health")
def health():

    return jsonify({
        "status": "success",
        "message": "Backend is healthy"
    })


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/api/dashboard")
def dashboard():

    # Import local storage functions

    from routes.patient_routes import read_patients

    patients = read_patients()


    high = 0
    medium = 0
    low = 0


    for patient in patients:

        risk = patient.get("risk_level")

        if risk == "HIGH":
            high += 1

        elif risk == "MEDIUM":
            medium += 1

        elif risk == "LOW":
            low += 1


    today = datetime.now().date()

    predictions_today = 0


    for patient in patients:

        created = patient.get("created_at", "")

        try:

            created_date = datetime.fromisoformat(
                created
            ).date()

            if created_date == today:
                predictions_today += 1

        except Exception:

            pass


    return jsonify({

        "status": "success",

        "total_patients": len(patients),

        "high_risk_patients": high,

        "medium_risk_patients": medium,

        "low_risk_patients": low,

        "predictions_today": predictions_today

    })


# =========================================================
# SAE PREDICTION
# =========================================================

@app.route("/api/predict", methods=["POST"])
def predict():

    patient_data = request.get_json()


    if not patient_data:

        return jsonify({

            "status": "error",

            "message": "No patient data received"

        }), 400


    try:

        prediction = prediction_service.predict_sae(
            patient_data
        )


        # Update local patient data

        patient_id = patient_data.get("patient_id")


        if patient_id:

            from routes.patient_routes import (
                read_patients,
                save_patients
            )


            patients = read_patients()


            for patient in patients:

                if patient.get("patient_id") == patient_id:

                    patient["risk_level"] = prediction["risk_level"]

                    patient["risk_score"] = prediction["risk_score"]

                    patient["updated_at"] = datetime.now().isoformat()


                    break


            save_patients(patients)


        return jsonify({

            "status": "success",

            "prediction": prediction,

            "database_updated": True

        })


    except Exception as e:

        return jsonify({

            "status": "error",

            "message": str(e)

        }), 500


# =========================================================
# ANALYTICS
# =========================================================

@app.route("/api/analytics")
def analytics():

    from routes.patient_routes import read_patients

    patients = read_patients()


    risk_distribution = {}

    gender_distribution = {}

    sepsis_distribution = {}

    age_distribution = {}


    for patient in patients:


        # Risk

        risk = patient.get("risk_level") or "NOT PREDICTED"

        risk_distribution[risk] = \
            risk_distribution.get(risk, 0) + 1


        # Gender

        gender = patient.get("gender") or "Not Specified"

        gender_distribution[gender] = \
            gender_distribution.get(gender, 0) + 1


        # Sepsis

        sepsis = patient.get("sepsis_status") or "Not Specified"

        sepsis_distribution[sepsis] = \
            sepsis_distribution.get(sepsis, 0) + 1


        # Age

        try:

            age = int(patient.get("age", 0))


            if age < 18:
                group = "Below 18"

            elif age <= 30:
                group = "18-30"

            elif age <= 45:
                group = "31-45"

            elif age <= 60:
                group = "46-60"

            else:
                group = "60+"


            age_distribution[group] = \
                age_distribution.get(group, 0) + 1

        except Exception:

            pass


    return jsonify({

        "status": "success",

        "risk_distribution": risk_distribution,

        "gender_distribution": gender_distribution,

        "sepsis_distribution": sepsis_distribution,

        "age_distribution": age_distribution

    })


# =========================================================
# REPORTS
# =========================================================

@app.route("/api/reports/patients")
def reports():

    from routes.patient_routes import read_patients

    patients = read_patients()


    return jsonify({

        "status": "success",

        "total": len(patients),

        "patients": patients

    })


# =========================================================
# START SERVER
# =========================================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )