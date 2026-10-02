CREATE DATABASE IF NOT EXISTS sae_prediction_system;

USE sae_prediction_system;

CREATE TABLE IF NOT EXISTS patients (
    id INT AUTO_INCREMENT PRIMARY KEY,

    patient_id VARCHAR(50) UNIQUE NOT NULL,

    name VARCHAR(100) NOT NULL,

    age INT NOT NULL,

    gender VARCHAR(20),

    sepsis_status VARCHAR(20),

    gcs INT,

    heart_rate FLOAT,

    blood_pressure VARCHAR(20),

    respiratory_rate FLOAT,

    spo2 FLOAT,

    temperature FLOAT,

    wbc FLOAT,

    lactate FLOAT,

    creatinine FLOAT,

    bilirubin FLOAT,

    platelets FLOAT,

    consciousness VARCHAR(50),

    risk_level VARCHAR(20),

    risk_score FLOAT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP
);