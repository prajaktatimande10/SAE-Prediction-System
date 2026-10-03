from flask import Blueprint, request, jsonify
from datetime import datetime

from database import get_db_connection

patient_routes = Blueprint("patient_routes", __name__)


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def format_datetime(value):
    """Convert MySQL datetime into JSON-friendly string."""
    if value is None:
        return None

    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")

    return str(value)


def convert_datetime(value):
    """
    Convert frontend datetime-local format:

        2026-10-04T14:30

    into MySQL format:

        2026-10-04 14:30:00
    """

    if not value:
        return None

    value = str(value).strip()

    try:
        value = value.replace("T", " ")

        if len(value) == 16:
            value += ":00"

        datetime.strptime(value, "%Y-%m-%d %H:%M:%S")

        return value

    except ValueError:
        return None


def convert_number(value, field_name, integer=False):
    """Safely convert numeric form values."""

    if value is None or value == "":
        return None

    try:
        if integer:
            return int(value)

        return float(value)

    except (ValueError, TypeError):
        raise ValueError(f"{field_name} must be a valid number")


# =========================================================
# GET ALL PATIENTS
# =========================================================

@patient_routes.route("/api/patients", methods=["GET"])
def get_patients():

    connection = get_db_connection()

    if connection is None:
        return jsonify({
            "status": "error",
            "message": "Database connection failed"
        }), 500

    cursor = None

    try:

        cursor = connection.cursor(dictionary=True)

        search = request.args.get("search", "").strip()

        if search:

            query = """
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
                WHERE
                    CAST(subject_id AS CHAR) LIKE %s
                    OR CAST(hadm_id AS CHAR) LIKE %s
                    OR CAST(stay_id AS CHAR) LIKE %s
                    OR gender LIKE %s
                ORDER BY id DESC
                LIMIT 1000
            """

            search_value = f"%{search}%"

            cursor.execute(
                query,
                (
                    search_value,
                    search_value,
                    search_value,
                    search_value
                )
            )

        else:

            query = """
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
            """

            cursor.execute(query)

        patients = cursor.fetchall()

        # Format values for JSON
        for patient in patients:

            patient["intime"] = format_datetime(
                patient.get("intime")
            )

            patient["outtime"] = format_datetime(
                patient.get("outtime")
            )

            if patient.get("age") is not None:
                patient["age"] = float(patient["age"])

            if patient.get("icu_los_hours") is not None:
                patient["icu_los_hours"] = float(
                    patient["icu_los_hours"]
                )

        # Total records
        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM icu_patients
        """)

        result = cursor.fetchone()

        total = result["total"]

        return jsonify({
            "status": "success",
            "patients": patients,
            "total": total,
            "returned": len(patients)
        })

    except Exception as error:

        print("GET PATIENTS ERROR:", error)

        return jsonify({
            "status": "error",
            "message": str(error)
        }), 500

    finally:

        if cursor:
            cursor.close()

        connection.close()


# =========================================================
# GET SINGLE PATIENT
# =========================================================

@patient_routes.route(
    "/api/patients/<int:patient_id>",
    methods=["GET"]
)
def get_patient(patient_id):

    connection = get_db_connection()

    if connection is None:
        return jsonify({
            "status": "error",
            "message": "Database connection failed"
        }), 500

    cursor = None

    try:

        cursor = connection.cursor(dictionary=True)

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
            WHERE id = %s
        """, (patient_id,))

        patient = cursor.fetchone()

        if patient is None:

            return jsonify({
                "status": "error",
                "message": "Patient not found"
            }), 404

        patient["intime"] = format_datetime(
            patient.get("intime")
        )

        patient["outtime"] = format_datetime(
            patient.get("outtime")
        )

        if patient.get("age") is not None:
            patient["age"] = float(patient["age"])

        if patient.get("icu_los_hours") is not None:
            patient["icu_los_hours"] = float(
                patient["icu_los_hours"]
            )

        return jsonify({
            "status": "success",
            "patient": patient
        })

    except Exception as error:

        print("GET PATIENT ERROR:", error)

        return jsonify({
            "status": "error",
            "message": str(error)
        }), 500

    finally:

        if cursor:
            cursor.close()

        connection.close()


# =========================================================
# ADD NEW PATIENT
# =========================================================

@patient_routes.route(
    "/api/patients",
    methods=["POST"]
)
def add_patient():

    data = request.get_json(silent=True)

    if not data:

        return jsonify({
            "status": "error",
            "message": "No patient data received"
        }), 400

    # -----------------------------------------------------
    # REQUIRED IDs
    # -----------------------------------------------------

    subject_id = data.get("subject_id")
    hadm_id = data.get("hadm_id")
    stay_id = data.get("stay_id")

    if subject_id is None or str(subject_id).strip() == "":
        return jsonify({
            "status": "error",
            "message": "Subject ID is required"
        }), 400

    if hadm_id is None or str(hadm_id).strip() == "":
        return jsonify({
            "status": "error",
            "message": "Admission ID is required"
        }), 400

    if stay_id is None or str(stay_id).strip() == "":
        return jsonify({
            "status": "error",
            "message": "ICU Stay ID is required"
        }), 400

    # -----------------------------------------------------
    # CONVERT IDs
    # -----------------------------------------------------

    try:

        subject_id = int(subject_id)
        hadm_id = int(hadm_id)
        stay_id = int(stay_id)

    except (ValueError, TypeError):

        return jsonify({
            "status": "error",
            "message": "Subject ID, Admission ID and ICU Stay ID must be numbers"
        }), 400

    # -----------------------------------------------------
    # DATETIME
    # -----------------------------------------------------

    intime = convert_datetime(
        data.get("intime")
    )

    outtime = convert_datetime(
        data.get("outtime")
    )

    if data.get("intime") and intime is None:

        return jsonify({
            "status": "error",
            "message": "Invalid ICU admission date/time"
        }), 400

    if data.get("outtime") and outtime is None:

        return jsonify({
            "status": "error",
            "message": "Invalid ICU discharge date/time"
        }), 400

    # -----------------------------------------------------
    # CHECK DATE ORDER
    # -----------------------------------------------------

    if intime and outtime:

        intime_dt = datetime.strptime(
            intime,
            "%Y-%m-%d %H:%M:%S"
        )

        outtime_dt = datetime.strptime(
            outtime,
            "%Y-%m-%d %H:%M:%S"
        )

        if outtime_dt < intime_dt:

            return jsonify({
                "status": "error",
                "message": "ICU discharge time cannot be earlier than ICU admission time"
            }), 400

    # -----------------------------------------------------
    # OTHER FIELDS
    # -----------------------------------------------------

    gender = data.get("gender")

    if gender:
        gender = str(gender).strip()

    if not gender:
        gender = None

    try:

        age = convert_number(
            data.get("age"),
            "Age"
        )

        icu_los_hours = convert_number(
            data.get("icu_los_hours"),
            "ICU length of stay"
        )

    except ValueError as error:

        return jsonify({
            "status": "error",
            "message": str(error)
        }), 400

    # -----------------------------------------------------
    # DATABASE CONNECTION
    # -----------------------------------------------------

    connection = get_db_connection()

    if connection is None:

        return jsonify({
            "status": "error",
            "message": "Database connection failed"
        }), 500

    cursor = None

    try:

        cursor = connection.cursor()

        # -------------------------------------------------
        # ONLY STAY ID MUST BE UNIQUE
        # -------------------------------------------------

        cursor.execute("""
            SELECT id
            FROM icu_patients
            WHERE stay_id = %s
        """, (stay_id,))

        existing = cursor.fetchone()

        if existing:

            return jsonify({
                "status": "error",
                "message": (
                    f"ICU Stay ID {stay_id} already exists. "
                    "Please use a different ICU Stay ID."
                )
            }), 409

        # -------------------------------------------------
        # INSERT NEW PATIENT
        # -------------------------------------------------

        cursor.execute("""
            INSERT INTO icu_patients
            (
                subject_id,
                hadm_id,
                stay_id,
                gender,
                age,
                intime,
                outtime,
                icu_los_hours
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )
        """, (
            subject_id,
            hadm_id,
            stay_id,
            gender,
            age,
            intime,
            outtime,
            icu_los_hours
        ))

        connection.commit()

        new_patient_id = cursor.lastrowid

        print(
            f"NEW PATIENT ADDED: "
            f"DB ID={new_patient_id}, "
            f"Subject ID={subject_id}, "
            f"Stay ID={stay_id}"
        )

        return jsonify({
            "status": "success",
            "message": "New patient added successfully",
            "id": new_patient_id,
            "patient": {
                "id": new_patient_id,
                "subject_id": subject_id,
                "hadm_id": hadm_id,
                "stay_id": stay_id,
                "gender": gender,
                "age": age,
                "intime": intime,
                "outtime": outtime,
                "icu_los_hours": icu_los_hours
            }
        }), 201

    except Exception as error:

        connection.rollback()

        print("ADD PATIENT ERROR:", error)

        return jsonify({
            "status": "error",
            "message": str(error)
        }), 500

    finally:

        if cursor:
            cursor.close()

        connection.close()


# =========================================================
# UPDATE PATIENT
# =========================================================

@patient_routes.route(
    "/api/patients/<int:patient_id>",
    methods=["PUT"]
)
def update_patient(patient_id):

    data = request.get_json(silent=True)

    if not data:

        return jsonify({
            "status": "error",
            "message": "No patient data received"
        }), 400

    connection = get_db_connection()

    if connection is None:

        return jsonify({
            "status": "error",
            "message": "Database connection failed"
        }), 500

    cursor = None

    try:

        cursor = connection.cursor()

        # -------------------------------------------------
        # CHECK PATIENT EXISTS
        # -------------------------------------------------

        cursor.execute("""
            SELECT id
            FROM icu_patients
            WHERE id = %s
        """, (patient_id,))

        if cursor.fetchone() is None:

            return jsonify({
                "status": "error",
                "message": "Patient not found"
            }), 404

        # -------------------------------------------------
        # VALUES
        # -------------------------------------------------

        subject_id = data.get("subject_id")
        hadm_id = data.get("hadm_id")
        stay_id = data.get("stay_id")

        try:

            subject_id = int(subject_id)
            hadm_id = int(hadm_id)
            stay_id = int(stay_id)

        except (ValueError, TypeError):

            return jsonify({
                "status": "error",
                "message": "Patient IDs must be numbers"
            }), 400

        # -------------------------------------------------
        # CHECK DUPLICATE STAY ID
        # -------------------------------------------------

        cursor.execute("""
            SELECT id
            FROM icu_patients
            WHERE stay_id = %s
            AND id != %s
        """, (stay_id, patient_id))

        duplicate = cursor.fetchone()

        if duplicate:

            return jsonify({
                "status": "error",
                "message": "Another patient already uses this ICU Stay ID"
            }), 409

        # -------------------------------------------------
        # DATETIME
        # -------------------------------------------------

        intime = convert_datetime(
            data.get("intime")
        )

        outtime = convert_datetime(
            data.get("outtime")
        )

        if data.get("intime") and intime is None:

            return jsonify({
                "status": "error",
                "message": "Invalid ICU admission date/time"
            }), 400

        if data.get("outtime") and outtime is None:

            return jsonify({
                "status": "error",
                "message": "Invalid ICU discharge date/time"
            }), 400

        if intime and outtime:

            intime_dt = datetime.strptime(
                intime,
                "%Y-%m-%d %H:%M:%S"
            )

            outtime_dt = datetime.strptime(
                outtime,
                "%Y-%m-%d %H:%M:%S"
            )

            if outtime_dt < intime_dt:

                return jsonify({
                    "status": "error",
                    "message": "ICU discharge time cannot be earlier than ICU admission time"
                }), 400

        # -------------------------------------------------
        # OTHER FIELDS
        # -------------------------------------------------

        gender = data.get("gender")

        if gender:
            gender = str(gender).strip()

        try:

            age = convert_number(
                data.get("age"),
                "Age"
            )

            icu_los_hours = convert_number(
                data.get("icu_los_hours"),
                "ICU length of stay"
            )

        except ValueError as error:

            return jsonify({
                "status": "error",
                "message": str(error)
            }), 400

        # -------------------------------------------------
        # UPDATE
        # -------------------------------------------------

        cursor.execute("""
            UPDATE icu_patients
            SET
                subject_id = %s,
                hadm_id = %s,
                stay_id = %s,
                gender = %s,
                age = %s,
                intime = %s,
                outtime = %s,
                icu_los_hours = %s
            WHERE id = %s
        """, (
            subject_id,
            hadm_id,
            stay_id,
            gender,
            age,
            intime,
            outtime,
            icu_los_hours,
            patient_id
        ))

        connection.commit()

        return jsonify({
            "status": "success",
            "message": "Patient updated successfully"
        })

    except Exception as error:

        connection.rollback()

        print("UPDATE PATIENT ERROR:", error)

        return jsonify({
            "status": "error",
            "message": str(error)
        }), 500

    finally:

        if cursor:
            cursor.close()

        connection.close()


# =========================================================
# DELETE PATIENT
# =========================================================

@patient_routes.route(
    "/api/patients/<int:patient_id>",
    methods=["DELETE"]
)
def delete_patient(patient_id):

    connection = get_db_connection()

    if connection is None:

        return jsonify({
            "status": "error",
            "message": "Database connection failed"
        }), 500

    cursor = None

    try:

        cursor = connection.cursor()

        cursor.execute("""
            DELETE FROM icu_patients
            WHERE id = %s
        """, (patient_id,))

        connection.commit()

        if cursor.rowcount == 0:

            return jsonify({
                "status": "error",
                "message": "Patient not found"
            }), 404

        return jsonify({
            "status": "success",
            "message": "Patient deleted successfully"
        })

    except Exception as error:

        connection.rollback()

        print("DELETE PATIENT ERROR:", error)

        return jsonify({
            "status": "error",
            "message": str(error)
        }), 500

    finally:

        if cursor:
            cursor.close()

        connection.close()