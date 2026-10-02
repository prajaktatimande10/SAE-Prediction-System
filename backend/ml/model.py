class SAEModel:
    """
    Temporary SAE prediction model.

    This class is structured so that a trained ML model
    can be connected later.
    """

    def __init__(self):
        self.model_name = "SAE Early Warning Model"

    def predict(self, patient_data):

        # ------------------------------------------------
        # Temporary rule-based prediction
        # ------------------------------------------------
        #
        # This is NOT a clinically validated SAE model.
        # It is only for testing the application pipeline.
        #

        heart_rate = float(patient_data.get("heart_rate", 80))
        respiratory_rate = float(patient_data.get("respiratory_rate", 18))
        temperature = float(patient_data.get("temperature", 37.0))
        spo2 = float(patient_data.get("spo2", 98))
        gcs = float(patient_data.get("gcs", 15))

        risk_score = 0

        # Example application-level rules
        if heart_rate > 100:
            risk_score += 20

        if respiratory_rate > 22:
            risk_score += 20

        if temperature > 38:
            risk_score += 15

        if spo2 < 94:
            risk_score += 20

        if gcs < 13:
            risk_score += 25

        # Keep score between 0 and 100
        risk_score = min(risk_score, 100)

        if risk_score >= 60:
            risk_level = "HIGH"

        elif risk_score >= 30:
            risk_level = "MEDIUM"

        else:
            risk_level = "LOW"

        return {
            "risk_score": risk_score,
            "risk_level": risk_level
        }