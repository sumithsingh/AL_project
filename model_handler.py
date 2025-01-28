import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import img_to_array
import numpy as np
from PIL import Image
import io
import logging
import os

class ModelHandler:
    def __init__(self):
        self.model = None
        self.classes = ['monocyte', 'myeloblast', 'erythroblast', 
                       'segmented_neutrophil', 'basophil']
        self.input_shape = (224, 224)
        self.load_model()

    def load_model(self):
        try:
            model_path = os.path.join('model', 'blood_cancer_model.keras')
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Model file not found at {model_path}")
            
            self.model = load_model(model_path)
            self.model.summary()  # Print model summary for verification
            logging.info("Model loaded successfully")
        except Exception as e:
            logging.error(f"Error loading model: {e}")
            raise

    def preprocess_image(self, image: Image.Image) -> np.ndarray:
        try:
            # Convert to grayscale (single channel)
            image = image.convert('L')
            
            # Resize to expected dimensions
            image = image.resize(self.input_shape)
            
            # Convert to array and add channel dimension
            img_array = img_to_array(image)
            
            # Ensure single channel and normalize
            img_array = img_array[..., np.newaxis] / 255.0
            
            # Add batch dimension
            img_array = np.expand_dims(img_array, axis=0)
            
            logging.info(f"Preprocessed image shape: {img_array.shape}")
            return img_array
        except Exception as e:
            logging.error(f"Error preprocessing image: {e}")
            raise

    def get_predictions(self, img_array: np.ndarray) -> np.ndarray:
        try:
            if self.model is None:
                raise ValueError("Model not loaded")
            
            # Verify input shape
            expected_shape = (1, 224, 224, 1)
            if img_array.shape != expected_shape:
                logging.error(f"Expected shape {expected_shape}, got {img_array.shape}")
                raise ValueError(f"Invalid input shape. Expected {expected_shape}, got {img_array.shape}")
            
            predictions = self.model.predict(img_array, verbose=0)
            return predictions[0]
        except Exception as e:
            logging.error(f"Error getting predictions: {e}")
            raise

    def assess_risk(self, predictions: np.ndarray) -> tuple:
        try:
            # Get myeloblast percentage
            myeloblast_idx = self.classes.index('myeloblast')
            myeloblast_percentage = predictions[myeloblast_idx] * 100

            # Risk assessment logic
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

    async def process_image(self, file) -> dict:
        try:
            # Read and process image
            image_data = await file.read()
            image = Image.open(io.BytesIO(image_data))
            
            # Preprocess image
            processed_image = self.preprocess_image(image)
            
            # Get predictions
            predictions = self.get_predictions(processed_image)
            
            # Assess risk level
            risk_level, risk_message = self.assess_risk(predictions)
            
            # Generate recommendations
            recommendations = self.generate_recommendations(risk_level)
            
            # Calculate cell counts
            cell_counts = {
                cell_type: float(pred * 100)
                for cell_type, pred in zip(self.classes, predictions)
            }
            
            # Prepare detailed results
            return {
                "cell_counts": cell_counts,
                "risk_assessment": f"{risk_level} Risk - {risk_message}",
                "recommendations": recommendations,
                "details": {
                    "myeloblast_percentage": cell_counts['myeloblast'],
                    "analysis_date": datetime.utcnow().isoformat(),
                    "confidence_score": float(np.max(predictions) * 100)
                }
            }
            
        except Exception as e:
            logging.error(f"Error processing image: {e}")
            raise HTTPException(status_code=500, detail=str(e))