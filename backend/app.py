from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime

from database import get_db_connection
from routes.patient_routes import patient_routes
from services.prediction_service import prediction_service


# ============================================================
# CREATE FLASK APPLICATION
# ============================================================

app = Flask(__name__)

# Allow frontend:
# http://localhost:3000
#
# to communicate with backend:
# http://127.0.0.1:5000

CORS(app)


# ============================================================
# REGISTER ROUTES
# ============================================================

app.register_blueprint(patient_routes)


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():

    return jsonify({
        "status": "success",
        "message": "SAE Prediction System Backend is running",
        "backend": "Flask",
        "database": "MySQL",
        "frontend": "HTML/CSS/JavaScript"
    })


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/api/health")
def health():

    return jsonify({
        "status": "success",
        "message": "Backend is healthy",
        "server": "127.0.0.1:5000"
    })


# ============================================================
# MYSQL DATABASE TEST
# ============================================================

@app.route("/api/database-test")
def database_test():

    connection = get_db_connection()

    if connection is None:

        return jsonify({
            "status": "error",
            "message": "Could not connect to MySQL"
        }), 500

    cursor = None

    try:

        cursor = connection.cursor()

        # Check database

        cursor.execute(
            "SELECT DATABASE()"
        )

        database_name = cursor.fetchone()[0]

        # Check number of records

        cursor.execute(
            "SELECT COUNT(*) FROM icu_patients"
        )

        total_records = cursor.fetchone()[0]

        return jsonify({

            "status": "success",

            "message":
                "Flask connected to MySQL successfully",

            "database":
                database_name,

            "table":
                "icu_patients",

            "total_records":
                total_records

        })

    except Exception as error:

        return jsonify({

            "status": "error",

            "message":
                str(error)

        }), 500

    finally:

        if cursor:
            cursor.close()

        connection.close()


# ============================================================
# DASHBOARD
# ============================================================

@app.route("/api/dashboard")
def dashboard():

    connection = get_db_connection()

    if connection is None:

        return jsonify({
            "status": "error",
            "message": "Database connection failed"
        }), 500

    cursor = None

    try:

        cursor = connection.cursor(dictionary=True)

        # ----------------------------------------------------
        # TOTAL ICU PATIENTS
        # ----------------------------------------------------

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM icu_patients
        """)

        total_patients = cursor.fetchone()["total"]


        # ----------------------------------------------------
        # AVERAGE AGE
        # ----------------------------------------------------

        cursor.execute("""
            SELECT
                ROUND(AVG(age), 2) AS average_age
            FROM icu_patients
            WHERE age IS NOT NULL
        """)

        average_age_result = cursor.fetchone()

        average_age = (
            average_age_result["average_age"]
            if average_age_result["average_age"] is not None
            else 0
        )


        # ----------------------------------------------------
        # AVERAGE ICU STAY
        # ----------------------------------------------------

        cursor.execute("""
            SELECT
                ROUND(AVG(icu_los_hours), 2)
                AS average_icu_hours
            FROM icu_patients
            WHERE icu_los_hours IS NOT NULL
        """)

        icu_result = cursor.fetchone()

        average_icu_hours = (
            icu_result["average_icu_hours"]
            if icu_result["average_icu_hours"] is not None
            else 0
        )


        # ----------------------------------------------------
        # MALE / FEMALE DISTRIBUTION
        # ----------------------------------------------------

        cursor.execute("""
            SELECT
                gender,
                COUNT(*) AS total
            FROM icu_patients
            GROUP BY gender
        """)

        gender_data = cursor.fetchall()


        # ----------------------------------------------------
        # RESPONSE
        # ----------------------------------------------------

        return jsonify({

            "status": "success",

            "total_patients":
                total_patients,

            "average_age":
                float(average_age),

            "average_icu_hours":
                float(average_icu_hours),

            "gender_distribution":
                gender_data,

            # These will be populated
            # after SAE prediction is connected.

            "high_risk_patients": 0,

            "medium_risk_patients": 0,

            "low_risk_patients": 0,

            "predictions_today": 0

        })

    except Exception as error:

        print(
            "DASHBOARD ERROR:",
            str(error)
        )

        return jsonify({

            "status": "error",

            "message":
                str(error)

        }), 500

    finally:

        if cursor:
            cursor.close()

        connection.close()


# ============================================================
# SAE PREDICTION
# ============================================================

@app.route(
    "/api/predict",
    methods=["POST"]
)
def predict():

    patient_data = request.get_json(
        silent=True
    )

    if not patient_data:

        return jsonify({

            "status": "error",

            "message":
                "No patient data received"

        }), 400


    try:

        # ----------------------------------------------------
        # RUN PREDICTION MODEL
        # ----------------------------------------------------

        prediction = (
            prediction_service.predict_sae(
                patient_data
            )
        )


        # ----------------------------------------------------
        # GET PATIENT ID
        # ----------------------------------------------------

        patient_id = patient_data.get(
            "patient_id"
        )


        # ----------------------------------------------------
        # TEMPORARY RESPONSE
        #
        # Database prediction update will be connected
        # in the MySQL patient route step.
        # ----------------------------------------------------

        return jsonify({

            "status": "success",

            "prediction":
                prediction,

            "patient_id":
                patient_id,

            "database_updated":
                False,

            "message":
                "Prediction generated successfully"

        })


    except Exception as error:

        print(
            "PREDICTION ERROR:",
            str(error)
        )

        return jsonify({

            "status": "error",

            "message":
                str(error)

        }), 500


# ============================================================
# ANALYTICS
# ============================================================

@app.route("/api/analytics")
def analytics():

    connection = get_db_connection()

    if connection is None:

        return jsonify({

            "status": "error",

            "message":
                "Database connection failed"

        }), 500


    cursor = None

    try:

        cursor = connection.cursor(
            dictionary=True
        )


        # ====================================================
        # GENDER DISTRIBUTION
        # ====================================================

        cursor.execute("""
            SELECT
                COALESCE(gender, 'Unknown')
                AS gender,
                COUNT(*) AS total
            FROM icu_patients
            GROUP BY gender
        """)

        gender_distribution = (
            cursor.fetchall()
        )


        # ====================================================
        # AGE DISTRIBUTION
        # ====================================================

        cursor.execute("""
            SELECT
                CASE

                    WHEN age < 18
                        THEN 'Below 18'

                    WHEN age BETWEEN 18 AND 30
                        THEN '18-30'

                    WHEN age BETWEEN 31 AND 45
                        THEN '31-45'

                    WHEN age BETWEEN 46 AND 60
                        THEN '46-60'

                    ELSE '60+'

                END AS age_group,

                COUNT(*) AS total

            FROM icu_patients

            WHERE age IS NOT NULL

            GROUP BY age_group

            ORDER BY age_group
        """)

        age_distribution = (
            cursor.fetchall()
        )


        # ====================================================
        # ICU LENGTH OF STAY GROUPS
        # ====================================================

        cursor.execute("""
            SELECT

                CASE

                    WHEN icu_los_hours < 24
                        THEN '< 24 hours'

                    WHEN icu_los_hours < 72
                        THEN '24-72 hours'

                    WHEN icu_los_hours < 168
                        THEN '3-7 days'

                    ELSE '> 7 days'

                END AS stay_group,

                COUNT(*) AS total

            FROM icu_patients

            WHERE icu_los_hours IS NOT NULL

            GROUP BY stay_group

        """)

        icu_stay_distribution = (
            cursor.fetchall()
        )


        # ====================================================
        # BASIC STATISTICS
        # ====================================================

        cursor.execute("""
            SELECT

                COUNT(*) AS total_patients,

                ROUND(
                    AVG(age),
                    2
                ) AS average_age,

                ROUND(
                    AVG(icu_los_hours),
                    2
                ) AS average_icu_hours,

                ROUND(
                    MIN(icu_los_hours),
                    2
                ) AS minimum_icu_hours,

                ROUND(
                    MAX(icu_los_hours),
                    2
                ) AS maximum_icu_hours

            FROM icu_patients
        """)

        statistics = cursor.fetchone()


        return jsonify({

            "status": "success",

            "statistics":
                statistics,

            "gender_distribution":
                gender_distribution,

            "age_distribution":
                age_distribution,

            "icu_stay_distribution":
                icu_stay_distribution,

            # SAE prediction analytics
            # will be added when model output
            # is stored in MySQL.

            "risk_distribution": {},

            "sepsis_distribution": {}

        })


    except Exception as error:

        print(
            "ANALYTICS ERROR:",
            str(error)
        )

        return jsonify({

            "status": "error",

            "message":
                str(error)

        }), 500


    finally:

        if cursor:
            cursor.close()

        connection.close()


# ============================================================
# REPORTS
# ============================================================

@app.route("/api/reports/patients")
def reports():

    connection = get_db_connection()

    if connection is None:

        return jsonify({

            "status": "error",

            "message":
                "Database connection failed"

        }), 500


    cursor = None

    try:

        cursor = connection.cursor(
            dictionary=True
        )


        cursor.execute("""
            SELECT

                id,

                subject_id,

                hadm_id,

                stay_id,

                gender,

                age,

                intime,

                outtime,

                icu_los_hours

            FROM icu_patients

            ORDER BY id DESC

            LIMIT 1000

        """)


        patients = cursor.fetchall()


        # Convert datetime objects
        # into JSON-compatible strings.

        for patient in patients:

            if patient.get("intime"):

                patient["intime"] = (
                    patient["intime"]
                    .isoformat()
                )

            if patient.get("outtime"):

                patient["outtime"] = (
                    patient["outtime"]
                    .isoformat()
                )


        return jsonify({

            "status": "success",

            "total":
                len(patients),

            "patients":
                patients

        })


    except Exception as error:

        print(
            "REPORT ERROR:",
            str(error)
        )

        return jsonify({

            "status": "error",

            "message":
                str(error)

        }), 500


    finally:

        if cursor:
            cursor.close()

        connection.close()


# ============================================================
# 404 ERROR
# ============================================================

@app.errorhandler(404)
def page_not_found(error):

    return jsonify({

        "status": "error",

        "message":
            "API endpoint not found"

    }), 404


# ============================================================
# 500 ERROR
# ============================================================

@app.errorhandler(500)
def internal_server_error(error):

    return jsonify({

        "status": "error",

        "message":
            "Internal server error"

    }), 500


# ============================================================
# START FLASK SERVER
# ============================================================

if __name__ == "__main__":

    print("")
    print("========================================")
    print("      SAE PREDICTION SYSTEM")
    print("========================================")
    print("Backend  : Flask")
    print("Database : MySQL")
    print("Frontend : HTML/CSS/JavaScript")
    print("Server   : http://127.0.0.1:5000")
    print("========================================")
    print("")

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )