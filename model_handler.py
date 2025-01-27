import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import img_to_array
import numpy as np
from PIL import Image
import io

class ModelHandler:
    def __init__(self):
        self.model = self.load_model()
        self.classes = ['monocyte', 'myeloblast', 'erythroblast', 
                       'segmented_neutrophil', 'basophil']
        
    def load_model(self):
        try:
            return load_model('model/blood_cancer_model.keras')
        except Exception as e:
            print(f"Error loading model: {e}")
            return None

    def preprocess_image(self, image):
        # Convert PIL Image to array
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Resize image to match model's expected input size
        image = image.resize((224, 224))  # Adjust size according to your model
        
        # Convert to array and preprocess
        img_array = img_to_array(image)
        img_array = np.expand_dims(img_array, axis=0)
        img_array = img_array / 255.0  # Normalize pixel values
        
        return img_array

    def get_predictions(self, img_array):
        predictions = self.model.predict(img_array)
        return predictions[0]

    def assess_risk(self, predictions):
        myeloblast_idx = self.classes.index('myeloblast')
        myeloblast_percentage = predictions[myeloblast_idx] * 100

        if myeloblast_percentage > 20:
            return "High", "Immediate medical attention required"
        elif myeloblast_percentage > 10:
            return "Moderate", "Further evaluation recommended"
        else:
            return "Low", "Regular monitoring advised"

    def generate_recommendations(self, risk_level):
        recommendations = {
            "High": [
                "Schedule immediate hematologist consultation",
                "Complete blood count (CBC) test recommended",
                "Bone marrow biopsy may be necessary",
                "Follow-up within 24-48 hours"
            ],
            "Moderate": [
                "Schedule follow-up within one week",
                "Regular blood count monitoring",
                "Track any new symptoms",
                "Prepare for additional testing if needed"
            ],
            "Low": [
                "Regular check-ups as scheduled",
                "Monitor for any changes in symptoms",
                "Maintain regular blood test schedule",
                "Follow healthy lifestyle recommendations"
            ]
        }
        return recommendations.get(risk_level, ["Consult with healthcare provider"])

    async def process_image(self, file):
        try:
            # Read and preprocess image
            image_data = await file.read()
            image = Image.open(io.BytesIO(image_data))
            processed_image = self.preprocess_image(image)
            
            # Check if model is loaded
            if self.model is None:
                raise Exception("Model not loaded properly")
            
            # Get predictions
            predictions = self.get_predictions(processed_image)
            
            # Create results dictionary
            cell_counts = {
                cell_type: float(pred * 100) 
                for cell_type, pred in zip(self.classes, predictions)
            }
            
            risk_level, risk_message = self.assess_risk(predictions)
            recommendations = self.generate_recommendations(risk_level)
            
            return {
                "cell_counts": cell_counts,
                "risk_assessment": f"{risk_level} Risk - {risk_message}",
                "recommendations": recommendations
            }
            
        except Exception as e:
            raise Exception(f"Error processing image: {str(e)}")

    def interpret_results(self, predictions):
        """Additional method to provide detailed interpretation of results"""
        interpretation = []
        for cell_type, percentage in zip(self.classes, predictions):
            if percentage > 0.1:  # 10% threshold for significance
                interpretation.append(f"{cell_type.title()}: {percentage*100:.1f}% detected")
        
        return "\n".join(interpretation)