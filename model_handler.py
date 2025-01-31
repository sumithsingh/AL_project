import os
import numpy as np
from tensorflow.keras.models import load_model
from PIL import Image
import io
import logging
from datetime import datetime
from fastapi import HTTPException

class ModelHandler:
    def __init__(self):
        self.model = None
        self.classes = ['monocyte', 'myeloblast', 'erythroblast', 'segmented_neutrophil', 'basophil']
        self.input_shape = (224, 224, 1)  # Ensure grayscale (1 channel)
        self.load_model()

    def load_model(self):
        try:
            model_path = os.path.join('model', 'blood_cancer_model.keras')
            if not os.path.exists(model_path):
                logging.error(f"Model file NOT found at {model_path}")
                raise FileNotFoundError(f"Model file not found at {model_path}")
            
            self.model = load_model(model_path)
            logging.info("✅ Model loaded successfully")
        except Exception as e:
            logging.error(f"❌ Error loading model: {e}")
            raise

    def preprocess_image(self, image: Image.Image) -> np.ndarray:
        try:
            image = image.convert('L')
            image = image.resize((224, 224))
            if image.size[0] < 100 or image.size[1] < 100:
                raise HTTPException(
                    status_code=400,
                    detail="Image resolution too low. Minimum 100x100 required."
                )
            img_array = np.array(image, dtype=np.float32) / 255.0
            img_array = img_array.reshape((224, 224, 1))
            img_array = np.expand_dims(img_array, axis=0)

            logging.info(f"🖼 Processed Image Shape: {img_array.shape}")
            return img_array
        except Exception as e:
            logging.error(f"❌ Error preprocessing image: {e}")
            raise

    def get_predictions(self, img_array: np.ndarray) -> np.ndarray:
        try:
            if self.model is None:
                logging.error("🚨 Model is not loaded!")
                raise ValueError("Model not loaded properly. Check if the model file exists.")

            if img_array.shape != (1, 224, 224, 1):  
                logging.error(f"❌ Invalid input shape: {img_array.shape}")
                raise ValueError(f"Invalid input shape: {img_array.shape}")

            logging.info("📊 Running model prediction...")
            predictions = self.model.predict(img_array, verbose=0)
            logging.info(f"🧬 Raw Predictions: {predictions}")

            if np.max(predictions) < 0.01:  # If all predictions are near zero
                logging.error("❌ Model returned low-confidence predictions")
                raise HTTPException(
                    status_code=500,
                    detail="Model couldn't make confident prediction. Check image quality."
                )

            if predictions is None or not isinstance(predictions, np.ndarray) or len(predictions) == 0:
                logging.error("❌ Model returned empty predictions!")
                raise ValueError("Model returned empty predictions.")

            return predictions[0]
        except Exception as e:
            logging.error(f"❌ Error getting predictions: {e}")
            raise

    def assess_risk(self, predictions: np.ndarray) -> tuple:
        try:
            if "myeloblast" not in self.classes:
                raise ValueError("Myeloblast class not found in model classes.")

            myeloblast_idx = self.classes.index('myeloblast')
            myeloblast_percentage = float(predictions[myeloblast_idx] * 100)

            logging.info(f"🔬 Myeloblast Percentage: {myeloblast_percentage}%")

            if myeloblast_percentage > 20:
                return "High", "Immediate medical attention required"
            elif myeloblast_percentage > 10:
                return "Moderate", "Further evaluation recommended"
            else:
                return "Low", "Regular monitoring advised"
        except Exception as e:
            logging.error(f"❌ Error assessing risk: {e}")
            raise

    def generate_recommendations(self, risk_level: str) -> list:
        recommendations = {
            "High": [
                "Schedule immediate hematologist consultation",
                "Complete blood count (CBC) test recommended",
                "Bone marrow biopsy may be necessary",
                "Follow-up within 24-48 hours",
                "Monitor for fever, fatigue, and unusual bleeding"
            ],
            "Moderate": [
                "Schedule follow-up within one week",
                "Regular blood count monitoring",
                "Track any new symptoms",
                "Additional testing may be needed",
                "Maintain detailed symptom diary"
            ],
            "Low": [
                "Continue regular check-ups as scheduled",
                "Monitor for any changes in symptoms",
                "Maintain regular blood test schedule",
                "Follow healthy lifestyle recommendations",
                "Report any new symptoms to healthcare provider"
            ]
        }
        return recommendations.get(risk_level, ["Consult with healthcare provider"])

    async def process_image(self, image_data: bytes) -> dict:
        try:
            image = Image.open(io.BytesIO(image_data))
            logging.info(f"Processing {image.format} image: {image.size}x{image.mode}")

            processed_image = self.preprocess_image(image)
            predictions = self.get_predictions(processed_image)

            cell_counts = {cell: float(pred * 100) for cell, pred in zip(self.classes, predictions)}
            risk_level, risk_message = self.assess_risk(predictions)
            confidence_score = float(np.max(predictions) * 100) if predictions.size > 0 else 0.0

            logging.info(f"Final Risk Level: {risk_level}, Confidence Score: {confidence_score}%")

            return {
                "id": datetime.utcnow().strftime("%Y%m%d%H%M%S"),
                "date": datetime.utcnow().isoformat(),
                "risk_level": risk_level,
                "results": {
                    "cell_counts": cell_counts,
                    "risk_assessment": f"{risk_level} Risk - {risk_message}",
                    "recommendations": self.generate_recommendations(risk_level),
                    "details": {
                        "myeloblast_percentage": cell_counts.get("myeloblast", 0),
                        "analysis_date": datetime.utcnow().isoformat(),
                        "confidence_score": confidence_score
                    }
                }
            }
        except Exception as e:
            logging.error(f"❌ Error processing image: {e}")
            raise
