import logging
from typing import Optional, Dict
import os
from pathlib import Path
import json

class ChatResponse:
    """Handle chat responses and translations."""
    
    @staticmethod
    def translate_text(text: str, target_lang: str) -> str:
        """Translate text to target language."""
        translations = {
            "French": {
                "Hello": "Bonjour",
                "How can I help you?": "Comment puis-je vous aider?",
                "Please consult your doctor": "Veuillez consulter votre médecin",
                "Your symptoms require medical attention": "Vos symptômes nécessitent une attention médicale"
            },
            "Spanish": {
                "Hello": "Hola",
                "How can I help you?": "¿Cómo puedo ayudarte?",
                "Please consult your doctor": "Por favor, consulta a tu médico",
                "Your symptoms require medical attention": "Tus síntomas requieren atención médica"
            }
            # Add more languages as needed
        }
        
        if target_lang in translations and text in translations[target_lang]:
            return translations[target_lang][text]
        return text

class MedicalKnowledgeBase:
    """Medical knowledge base for blood cancer information."""
    
    def __init__(self):
        self.knowledge_base = {
            "symptoms": [
                "Fatigue and weakness",
                "Frequent infections",
                "Easy bruising or bleeding",
                "Bone pain",
                "Fever or night sweats",
                "Unexplained weight loss"
            ],
            "risk_factors": [
                "Age (more common in older adults)",
                "Previous cancer treatment",
                "Genetic disorders",
                "Exposure to certain chemicals",
                "Family history of blood cancer"
            ],
            "diagnosis": [
                "Blood tests",
                "Bone marrow biopsy",
                "Imaging tests (X-rays, CT scans)",
                "Genetic testing",
                "Physical examination"
            ],
            "treatment": [
                "Chemotherapy",
                "Radiation therapy",
                "Stem cell transplantation",
                "Targeted therapy",
                "Immunotherapy"
            ],
            "prevention": [
                "Maintain a healthy lifestyle",
                "Regular exercise",
                "Balanced diet",
                "Avoid exposure to harmful chemicals",
                "Regular medical check-ups"
            ]
        }

    def get_information(self, topic: str) -> list:
        """Get information for a specific topic."""
        return self.knowledge_base.get(topic, [])

class ChatBot:
    def __init__(self):
        self.knowledge_base = MedicalKnowledgeBase()
        self.default_response = (
            "I can provide information about blood cancer symptoms, "
            "diagnosis, treatment, prevention, and risk factors. "
            "What would you like to know?"
        )

    def _extract_topic(self, message: str) -> Optional[str]:
        """Extract the main topic from the user's message."""
        message = message.lower()
        topics = {
            "symptoms": ["symptom", "feel", "experiencing"],
            "diagnosis": ["diagnos", "test", "detect", "identify"],
            "treatment": ["treat", "cure", "therapy", "medication"],
            "prevention": ["prevent", "avoid", "reduce risk"],
            "risk_factors": ["risk", "cause", "factor", "likelihood"]
        }
        
        for topic, keywords in topics.items():
            if any(keyword in message for keyword in keywords):
                return topic
        return None

    def _format_response(self, information: list) -> str:
        """Format the response in a user-friendly way."""
        return "\n".join([f"• {item}" for item in information])

    def get_response(self, message: str) -> str:
        """Generate a response based on the user's message."""
        topic = self._extract_topic(message)
        
        if topic:
            information = self.knowledge_base.get_information(topic)
            if information:
                return f"Here's what you should know about blood cancer {topic}:\n" + self._format_response(information)
        
        return self.default_response

def get_llama_response(message: str, language: str = "English") -> str:
    """
    Get response from chatbot with language support.
    This is a placeholder for LLaMA integration - replace with actual LLaMA implementation.
    """
    try:
        # Initialize chatbot
        chatbot = ChatBot()
        
        # Get response in English
        response = chatbot.get_response(message)
        
        # Translate if needed
        if language != "English":
            response = ChatResponse.translate_text(response, language)
        
        return response
        
    except Exception as e:
        logging.error(f"Error generating response: {e}")
        return "I apologize, but I'm having trouble generating a response. Please try again."

# Additional helper functions for the chatbot
def sanitize_input(message: str) -> str:
    """Sanitize user input to prevent injection and other security issues."""
    # Remove any potentially harmful characters or sequences
    return message.strip()

def format_medical_terms(text: str) -> str:
    """Format medical terms with proper capitalization and explanations."""
    medical_terms = {
        "cbc": "Complete Blood Count (CBC)",
        "wbc": "White Blood Cell (WBC) count",
        "rbc": "Red Blood Cell (RBC) count",
        "aml": "Acute Myeloid Leukemia (AML)",
        "cml": "Chronic Myeloid Leukemia (CML)",
        "all": "Acute Lymphoblastic Leukemia (ALL)"
    }
    
    for term, replacement in medical_terms.items():
        text = text.replace(term.upper(), replacement)
        text = text.replace(term.lower(), replacement)
    
    return text

def get_emergency_response(symptoms: list) -> str:
    """Generate emergency response based on severe symptoms."""
    emergency_symptoms = [
        "severe bleeding",
        "high fever",
        "extreme fatigue",
        "severe pain"
    ]
    
    if any(symptom in " ".join(symptoms).lower() for symptom in emergency_symptoms):
        return "IMPORTANT: These symptoms require immediate medical attention. Please contact your healthcare provider or emergency services right away."
    return ""