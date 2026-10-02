from flask import Blueprint, request, jsonify
import json
import os
from datetime import datetime

patient_routes = Blueprint("patient_routes", __name__)

# ---------------------------------------------------------
# LOCAL DATA FILE
# ---------------------------------------------------------

DATA_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "data",
    "patients.json"
)


# ---------------------------------------------------------
# MAKE SURE DATA FILE EXISTS
# ---------------------------------------------------------

def initialize_data_file():

    data_folder = os.path.dirname(DATA_FILE)

    if not os.path.exists(data_folder):
        os.makedirs(data_folder)

    if not os.path.exists(DATA_FILE):

        with open(DATA_FILE, "w") as file:
            json.dump([], file, indent=4)


# ---------------------------------------------------------
# READ PATIENTS
# ---------------------------------------------------------

def read_patients():

    initialize_data_file()

    try:

        with open(DATA_FILE, "r") as file:

            data = json.load(file)

            if isinstance(data, list):
                return data

            return []

    except Exception:

        return []


# ---------------------------------------------------------
# SAVE PATIENTS
# ---------------------------------------------------------

def save_patients(patients):

    initialize_data_file()

    with open(DATA_FILE, "w") as file:

        json.dump(
            patients,
            file,
            indent=4
        )


# ---------------------------------------------------------
# GET ALL PATIENTS
# ---------------------------------------------------------

@patient_routes.route("/api/patients", methods=["GET"])
def get_patients():

    patients = read_patients()

    return jsonify({
        "status": "success",
        "patients": patients,
        "total": len(patients)
    })


# ---------------------------------------------------------
# GET SINGLE PATIENT
# ---------------------------------------------------------

@patient_routes.route("/api/patients/<int:patient_id>", methods=["GET"])
def get_patient(patient_id):

    patients = read_patients()

    patient = next(
        (
            p for p in patients
            if p.get("id") == patient_id
        ),
        None
    )

    if patient is None:

        return jsonify({
            "status": "error",
            "message": "Patient not found"
        }), 404

    return jsonify({
        "status": "success",
        "patient": patient
    })


# ---------------------------------------------------------
# ADD PATIENT
# ---------------------------------------------------------

@patient_routes.route("/api/patients", methods=["POST"])
def add_patient():

    data = request.get_json()

    if not data:

        return jsonify({
            "status": "error",
            "message": "No patient data received"
        }), 400


    patient_id = data.get("patient_id")
    name = data.get("name")
    age = data.get("age")


    if not patient_id:

        return jsonify({
            "status": "error",
            "message": "Patient ID is required"
        }), 400


    if not name:

        return jsonify({
            "status": "error",
            "message": "Patient name is required"
        }), 400


    if age is None or age == "":

        return jsonify({
            "status": "error",
            "message": "Patient age is required"
        }), 400


    patients = read_patients()


    # Check duplicate patient ID

    for patient in patients:

        if patient.get("patient_id") == patient_id:

            return jsonify({
                "status": "error",
                "message": "Patient ID already exists"
            }), 409


    # Generate local numeric ID

    if patients:

        new_id = max(
            p.get("id", 0)
            for p in patients
        ) + 1

    else:

        new_id = 1


    new_patient = {

        "id": new_id,

        "patient_id": patient_id,

        "name": name,

        "age": age,

        "gender": data.get("gender"),

        "sepsis_status": data.get("sepsis_status"),

        "gcs": data.get("gcs"),

        "heart_rate": data.get("heart_rate"),

        "blood_pressure": data.get("blood_pressure"),

        "respiratory_rate": data.get("respiratory_rate"),

        "spo2": data.get("spo2"),

        "temperature": data.get("temperature"),

        "wbc": data.get("wbc"),

        "lactate": data.get("lactate"),

        "creatinine": data.get("creatinine"),

        "bilirubin": data.get("bilirubin"),

        "platelets": data.get("platelets"),

        "consciousness": data.get("consciousness"),

        "risk_level": data.get("risk_level"),

        "risk_score": data.get("risk_score"),

        "created_at": datetime.now().isoformat(),

        "updated_at": datetime.now().isoformat()
    }


    patients.append(new_patient)

    save_patients(patients)


    return jsonify({

        "status": "success",

        "message": "Patient stored locally",

        "patient": new_patient

    }), 201


# ---------------------------------------------------------
# UPDATE PATIENT
# ---------------------------------------------------------

@patient_routes.route("/api/patients/<int:patient_id>", methods=["PUT"])
def update_patient(patient_id):

    data = request.get_json()

    patients = read_patients()


    patient = next(
        (
            p for p in patients
            if p.get("id") == patient_id
        ),
        None
    )


    if patient is None:

        return jsonify({
            "status": "error",
            "message": "Patient not found"
        }), 404


    # Update supplied fields

    fields = [

        "patient_id",
        "name",
        "age",
        "gender",
        "sepsis_status",
        "gcs",
        "heart_rate",
        "blood_pressure",
        "respiratory_rate",
        "spo2",
        "temperature",
        "wbc",
        "lactate",
        "creatinine",
        "bilirubin",
        "platelets",
        "consciousness",
        "risk_level",
        "risk_score"

    ]


    for field in fields:

        if field in data:

            patient[field] = data[field]


    patient["updated_at"] = datetime.now().isoformat()


    save_patients(patients)


    return jsonify({

        "status": "success",

        "message": "Patient updated successfully",

        "patient": patient

    })


# ---------------------------------------------------------
# DELETE PATIENT
# ---------------------------------------------------------

@patient_routes.route("/api/patients/<int:patient_id>", methods=["DELETE"])
def delete_patient(patient_id):

    patients = read_patients()


    new_patients = [

        p for p in patients
        if p.get("id") != patient_id

    ]


    if len(new_patients) == len(patients):

        return jsonify({

            "status": "error",

            "message": "Patient not found"

        }), 404


    save_patients(new_patients)


    return jsonify({

        "status": "success",

        "message": "Patient deleted successfully"

    })