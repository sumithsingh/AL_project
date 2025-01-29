import logging
from typing import Dict, List, Optional
from datetime import datetime
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class LanguageHandler:
    """Handles translations and language-specific responses."""
    
    translations = {
        "French": {
            "Hello": "Bonjour",
            "Emergency Alert": "Alerte d'urgence",
            "Medical Attention Required": "Attention médicale requise",
            "Symptoms": "Symptômes",
            "Treatment": "Traitement",
            "Diagnosis": "Diagnostic",
            "Prevention": "Prévention",
            "Please consult a doctor": "Veuillez consulter un médecin"
        },
        "Spanish": {
            "Hello": "Hola",
            "Emergency Alert": "Alerta de Emergencia",
            "Medical Attention Required": "Atención Médica Requerida",
            "Symptoms": "Síntomas",
            "Treatment": "Tratamiento",
            "Diagnosis": "Diagnóstico",
            "Prevention": "Prevención",
            "Please consult a doctor": "Por favor consulte a un médico"
        }
    }
    
    emergency_keywords = {
        "English": ["emergency", "severe", "urgent", "critical", "immediate", "life-threatening"],
        "Spanish": ["emergencia", "grave", "urgente", "crítico", "inmediato", "riesgo vital"],
        "French": ["urgence", "grave", "urgent", "critique", "immédiat", "danger de mort"]
    }
    
    @classmethod
    def translate(cls, text: str, target_lang: str) -> str:
        """Translate text to target language."""
        if target_lang == "English":
            return text
        
        translations = cls.translations.get(target_lang, {})
        for eng, trans in translations.items():
            text = text.replace(eng, trans)
        return text
    
    @classmethod
    def is_emergency(cls, query: str, language: str = "English") -> bool:
        """Check if query indicates emergency in specified language."""
        query = query.lower()
        keywords = cls.emergency_keywords.get(language, cls.emergency_keywords["English"])
        return any(keyword in query for keyword in keywords + ["immediate help", "911", "emergency room"])

class MedicalKnowledgeBase:
    """Medical knowledge base with comprehensive blood cancer information."""
    
    def __init__(self):
        self.knowledge_base = {
            "general": {
                "overview": [
                    "Blood cancer affects the blood cells and bone marrow",
                    "There are three main types: leukemia, lymphoma, and myeloma",
                    "Early detection significantly improves treatment outcomes",
                    "Regular monitoring and follow-up care are essential",
                    "Treatment plans are tailored to each patient's condition"
                ]
            },
            "symptoms": {
                "common": [
                    "Persistent fatigue and weakness",
                    "Frequent or recurring infections",
                    "Easy bruising or bleeding",
                    "Bone or joint pain",
                    "Night sweats and fever",
                    "Unexplained weight loss",
                    "Swollen lymph nodes",
                    "Shortness of breath",
                    "Pale skin",
                    "Frequent nosebleeds"
                ],
                "emergency": [
                    "Severe uncontrolled bleeding",
                    "High fever with chills",
                    "Extreme difficulty breathing",
                    "Severe chest pain",
                    "Loss of consciousness",
                    "Severe abdominal pain"
                ]
            },
            "diagnosis": {
                "tests": [
                    "Complete Blood Count (CBC)",
                    "Bone Marrow Biopsy",
                    "Flow Cytometry",
                    "Genetic Testing",
                    "Imaging Tests (CT, MRI, PET)",
                    "Lymph Node Biopsy"
                ],
                "procedures": [
                    "Physical examination",
                    "Medical history review",
                    "Blood smear analysis",
                    "Molecular testing",
                    "Immunophenotyping"
                ]
            },
            "treatment": {
                "primary": [
                    "Chemotherapy",
                    "Radiation Therapy",
                    "Stem Cell Transplantation",
                    "Targeted Therapy",
                    "Immunotherapy",
                    "CAR T-cell Therapy"
                ],
                "supportive": [
                    "Blood transfusions",
                    "Pain management",
                    "Antibiotic therapy",
                    "Nutritional support",
                    "Physical therapy",
                    "Psychological support"
                ]
            },
            "prevention": {
                "lifestyle": [
                    "Maintain a healthy diet",
                    "Regular exercise",
                    "Adequate rest and sleep",
                    "Stress management",
                    "Regular medical check-ups"
                ],
                "risk_factors": [
                    "Family history of blood cancer",
                    "Previous cancer treatment",
                    "Exposure to certain chemicals",
                    "Genetic syndromes",
                    "Smoking and tobacco use",
                    "Radiation exposure"
                ]
            }
        }
        
        self.topic_matches = {
            "symptoms": ["symptom", "sign", "feel", "experience"],
            "diagnosis": ["diagnos", "test", "detect", "examine"],
            "treatment": ["treat", "therapy", "cure", "medicine"],
            "prevention": ["prevent", "avoid", "protect", "risk"],
            "general": ["what is", "about", "tell me", "explain"]
        }
        
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            stop_words='english',
            max_features=10000
        )
        self._prepare_search_corpus()
    
    def _prepare_search_corpus(self):
        """Prepare search corpus with context."""
        self.search_corpus = []
        self.corpus_mappings = []
        
        for category, subcategories in self.knowledge_base.items():
            for subcategory, items in subcategories.items():
                for item in items:
                    search_text = f"{category} {subcategory} {item}".lower()
                    self.search_corpus.append(search_text)
                    self.corpus_mappings.append({
                        'category': category,
                        'subcategory': subcategory,
                        'text': item,
                        'context': f"{category} {subcategory}"
                    })
        
        if self.search_corpus:
            self.tfidf_matrix = self.vectorizer.fit_transform(self.search_corpus)

    def _get_topic(self, query: str) -> str:
        """Determine the topic of the query."""
        query = query.lower()
        for topic, keywords in self.topic_matches.items():
            if any(keyword in query for keyword in keywords):
                return topic
        return "general"

    def find_relevant_information(self, query: str, threshold: float = 0.2) -> List[Dict]:
        """Find relevant information for the query."""
        try:
            query_lower = query.lower()
            topic = self._get_topic(query_lower)
            
            # Get vector similarity
            query_vector = self.vectorizer.transform([query_lower])
            similarities = cosine_similarity(query_vector, self.tfidf_matrix).flatten()
            
            relevant_info = []
            for idx, score in enumerate(similarities):
                if score > threshold:
                    info = self.corpus_mappings[idx].copy()
                    info['relevance_score'] = float(score)
                    
                    # Boost score for topic matches
                    if info['category'] == topic:
                        info['relevance_score'] *= 2
                    
                    relevant_info.append(info)
            
            # Sort by relevance
            sorted_info = sorted(relevant_info, key=lambda x: x['relevance_score'], reverse=True)
            
            # Return top 5 results
            return sorted_info[:5]
            
        except Exception as e:
            logging.error(f"Search error: {e}")
            return []

class FreeMedicalChatbot:
    """Medical chatbot with enhanced response handling."""
    
    def __init__(self):
        self.kb = MedicalKnowledgeBase()
        self.lang_handler = LanguageHandler()
        self.conversation_history = []
        self.max_history = 5
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("MedicalChatbot")
    
    def _format_response(self, info_list: List[Dict], query: str) -> str:
        """Format information into a readable response."""
        # Handle empty results with topic-specific responses
        if not info_list:
            query_lower = query.lower()
            if "symptom" in query_lower:
                return "\n".join([
                    "Common blood cancer symptoms include:",
                    "• Persistent fatigue and weakness",
                    "• Frequent infections",
                    "• Easy bruising or bleeding",
                    "• Bone/joint pain",
                    "• Night sweats and fever",
                    "• Unexplained weight loss"
                ])
                
            elif "prevent" in query_lower:
                return "\n".join([
                    "Blood cancer prevention measures include:",
                    "• Maintain a healthy lifestyle",
                    "• Regular exercise and balanced diet",
                    "• Regular medical check-ups",
                    "• Avoid exposure to harmful chemicals",
                    "• Monitor for early warning signs"
                ])
                
            elif "treat" in query_lower:
                return "\n".join([
                    "Blood cancer treatment options include:",
                    "• Chemotherapy",
                    "• Radiation Therapy",
                    "• Stem Cell Transplantation",
                    "• Targeted Therapy",
                    "• Immunotherapy"
                ])
                
            elif "diagnos" in query_lower:
                return "\n".join([
                    "Blood cancer diagnosis involves:",
                    "• Complete Blood Count (CBC)",
                    "• Bone Marrow Biopsy",
                    "• Flow Cytometry",
                    "• Genetic Testing",
                    "• Imaging Tests"
                ])
            
            return "I can provide information about blood cancer symptoms, diagnosis, treatment, and prevention. What would you like to know?"

        # Group information by category
        categories = {}
        for info in info_list:
            cat = info['category']
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(info['text'])

        # Format response with categories and bullet points
        response_parts = []
        for category, items in categories.items():
            category_title = category.title()
            section = [f"{category_title} Information:"]
            section.extend([f"• {item}" for item in items[:3]])
            response_parts.append("\n".join(section))

        return "\n\n".join(response_parts)
    
    def get_response(self, query: str, language: str = "English") -> Dict:
        """Generate response for user query."""
        try:
            # Check for emergency
            if self.lang_handler.is_emergency(query, language):
                emergency_msg = "EMERGENCY: Please seek immediate medical attention!"
                if language != "English":
                    emergency_msg = self.lang_handler.translate(emergency_msg, language)
                return {
                    "response": emergency_msg,
                    "is_emergency": True,
                    "language": language
                }
            
            # Get relevant information
            relevant_info = self.kb.find_relevant_information(query)
            
            # Format response
            response = self._format_response(relevant_info, query)
            if language != "English":
                response = self.lang_handler.translate(response, language)
            
            # Update conversation history
            self.conversation_history.append({
                'query': query,
                'response': response,
                'timestamp': datetime.utcnow().isoformat()
            })
            
            # Maintain history limit
            if len(self.conversation_history) > self.max_history:
                self.conversation_history = self.conversation_history[-self.max_history:]
            
            return {
                "response": response,
                "is_emergency": False,
                "relevant_info": relevant_info,
                "language": language,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Chat error: {e}")
            return {
                "response": "I apologize, but I'm having trouble processing your request. Please try again.",
                "error": str(e)
            }