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
        # Ensure 'erythroblast' is included as a class
        self.classes = ['monocyte', 'myeloblast', 'erythroblast', 'segmented_neutrophil', 'basophil']
        self.input_shape = (224, 224)  # Resize to this shape
        self.load_model()

    def load_model(self):
        try:
            model_path = os.path.join('model', 'blood_cancer_model.keras')  # Ensure the correct path
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Model file not found at {model_path}")
            
            self.model = load_model(model_path)
            self.model.summary()
            logging.info("Model loaded successfully")
        except Exception as e:
            logging.error(f"Error loading model: {e}")
            raise

    def preprocess_image(self, image: Image.Image) -> np.ndarray:
        try:
            # Convert to RGB (remove grayscale conversion)
            if image.mode != 'L':
                image = image.convert('L')  # Ensure 1 channels
            # Resize to model's input shape
            image = image.resize(self.input_shape)
        
            # Convert to array and normalize
            img_array = np.array(image)
            img_array = img_array.astype(float) / 255.0
            img_array = img_array.reshape((224, 224, 1))  # 1 channels for RGB
            return img_array
        
        except Exception as e:
            logging.error(f"Error preprocessing image: {e}")
            raise

    def get_predictions(self, img_array: np.ndarray) -> np.ndarray:
        try:
            if self.model is None:
                raise ValueError("Model not loaded")

            # Update input shape validation (3 channels instead of 1)
            if img_array.shape != (1, 224, 224, 3):  # Changed from (1, 224, 224, 1)
                logging.error(f"Invalid input shape: {img_array.shape}")
                raise ValueError(f"Invalid input shape: {img_array.shape}")

            # Get predictions from the model
            predictions = self.model.predict(img_array, verbose=0)
            logging.info(f"Prediction shape: {predictions.shape}")
            return predictions[0]
        except Exception as e:
            logging.error(f"Error getting predictions: {e}")
            raise

    def assess_risk(self, predictions: np.ndarray) -> tuple:
        try:
            # Assess risk based on myeloblast percentage
            myeloblast_idx = self.classes.index('myeloblast')
            myeloblast_percentage = float(predictions[myeloblast_idx] * 100)

            if myeloblast_percentage > 20:
                return "High", "Immediate medical attention required"
            elif myeloblast_percentage > 10:
                return "Moderate", "Further evaluation recommended"
            else:
                return "Low", "Regular monitoring advised"
        except Exception as e:
            logging.error(f"Error assessing risk: {e}")
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
            # Read and process the image file
            image = Image.open(io.BytesIO(image_data))

            # Log image details for debugging
            logging.info(f"Processing {image.format} image: {image.size}x{image.mode}")

            # Preprocess the image to fit the model's input shape
            processed_image = self.preprocess_image(image)

            # Get the model's predictions
            predictions = self.get_predictions(processed_image)

            # Assess risk and provide recommendations
            risk_level, risk_message = self.assess_risk(predictions)
            #recommendations = self.generate_recommendations(risk_level)

            # Prepare the results
            return {
                "cell_counts": {cell: float(pred*100) for cell, pred in zip(self.classes, predictions)},
                "risk_assessment": f"{risk_level} Risk - {risk_message}",
                "recommendations": self.generate_recommendations(risk_level),
                "details": {
                    "analysis_date": datetime.utcnow().isoformat(),
                    "confidence_score": float(np.max(predictions) * 100)
                }
            }
        except Exception as e:
            logging.error(f"Error processing image: {e}")
            raise