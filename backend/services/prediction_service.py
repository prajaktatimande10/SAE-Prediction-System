from ml.model import SAEModel


class PredictionService:

    def __init__(self):
        self.model = SAEModel()

    def predict_sae(self, patient_data):

        prediction = self.model.predict(patient_data)

        return {
            "risk_level": prediction["risk_level"],
            "risk_score": prediction["risk_score"],
            "model": "SAE Early Warning Model"
        }


# Create one service instance
prediction_service = PredictionService()