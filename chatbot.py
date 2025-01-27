# chatbot.py
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

class ChatBot:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.knowledge_base = self.load_knowledge_base()

    def load_knowledge_base(self):
        return {
            "blood_cancer": {
                "general_info": "Blood cancer affects blood cell production...",
                "cell_types": {
                    "myeloblast": "Immature white blood cells...",
                    "monocyte": "Type of white blood cell that fights infections...",
                    "erythroblast": "Develops into red blood cells...",
                    "neutrophil": "Most common type of white blood cell...",
                    "basophil": "Least common type of white blood cell..."
                },
                "risk_levels": {
                    "high": "Requires immediate medical attention...",
                    "moderate": "Needs careful monitoring...",
                    "low": "Regular check-ups recommended..."
                }
            }
        }

    async def get_response(self, message: str) -> str:
        try:
            # For now, return basic responses based on keywords
            message = message.lower()
            
            if 'risk' in message:
                return "Risk levels are categorized as High, Moderate, or Low based on cell counts."
            elif 'treatment' in message:
                return "Treatment options depend on the diagnosis and risk level."
            elif 'symptoms' in message:
                return "Common symptoms include fatigue, frequent infections, and unusual bleeding."
            else:
                return "I understand you have a question about blood cancer. Could you be more specific?"
            
        except Exception as e:
            print(f"Error in get_response: {e}")
            return "I apologize, but I'm having trouble processing your request. Please try again."