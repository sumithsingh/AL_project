from typing import Optional, Dict, List
import logging
from datetime import datetime
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

class MedicalKnowledgeBase:
    """Enhanced medical knowledge base with detailed blood cancer information."""
    
    def __init__(self):
        self.knowledge_base = {
            "symptoms": {
                "common": [
                    "Persistent fatigue and weakness",
                    "Unexplained weight loss",
                    "Frequent infections",
                    "Easy bruising or bleeding",
                    "Bone/joint pain",
                    "Night sweats",
                    "Enlarged lymph nodes"
                ],
                "emergency": [
                    "Severe bleeding",
                    "High fever with chills",
                    "Extreme fatigue",
                    "Severe bone pain",
                    "Difficulty breathing",
                    "Sudden weight loss"
                ]
            },
            "diagnosis": {
                "tests": [
                    "Complete Blood Count (CBC)",
                    "Bone Marrow Biopsy",
                    "Flow Cytometry",
                    "Genetic Testing",
                    "Imaging Tests (CT, MRI, PET)"
                ]
            },
            "treatment": {
                "standard": [
                    "Chemotherapy",
                    "Radiation Therapy",
                    "Targeted Therapy",
                    "Immunotherapy",
                    "Stem Cell Transplantation"
                ]
            }
        }
        
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 3))
        self._prepare_search_corpus()
    
    def _prepare_search_corpus(self):
        """Prepare search corpus for TF-IDF matching."""
        self.search_corpus = []
        self.corpus_mappings = []
        
        for category, subcategories in self.knowledge_base.items():
            for subcategory, items in subcategories.items():
                for item in items:
                    self.search_corpus.append(item.lower())
                    self.corpus_mappings.append((category, subcategory))
        
        if self.search_corpus:
            self.tfidf_matrix = self.vectorizer.fit_transform(self.search_corpus)
    
    def find_relevant_information(self, query: str, threshold: float = 0.3) -> List[Dict]:
        """Find relevant information based on the query using TF-IDF similarity."""
        if not self.search_corpus:
            return []
        
        query_vector = self.vectorizer.transform([query.lower()])
        similarities = cosine_similarity(query_vector, self.tfidf_matrix).flatten()
        
        relevant_info = []
        for idx, score in enumerate(similarities):
            if score > threshold:
                category, subcategory = self.corpus_mappings[idx]
                relevant_info.append({
                    'category': category,
                    'subcategory': subcategory,
                    'information': self.search_corpus[idx],
                    'relevance_score': float(score)
                })
        
        return sorted(relevant_info, key=lambda x: x['relevance_score'], reverse=True)

class FreeMedicalChatbot:
    """Medical chatbot using a lightweight, efficient free model."""
    
    def __init__(self):
        self.knowledge_base = MedicalKnowledgeBase()
        self.conversation_history = []
        self.max_history = 5
        self.emergency_keywords = [
            "emergency", "severe", "urgent", "critical",
            "extreme", "life-threatening", "immediate"
        ]
        
        try:
            self.tokenizer = AutoTokenizer.from_pretrained("google/flan-t5-small")
            self.model = AutoModelForSeq2SeqLM.from_pretrained("google/flan-t5-small")
        except Exception as e:
            logging.error(f"Error loading model: {e}")
            raise
    
    def _check_emergency(self, query: str) -> bool:
        """Check if query indicates a medical emergency."""
        return any(keyword in query.lower() for keyword in self.emergency_keywords)
    
    def _generate_response(self, prompt: str) -> str:
        """Generate response using the FLAN-T5 model."""
        try:
            inputs = self.tokenizer(prompt, return_tensors="pt", padding=True, truncation=True, max_length=256)
            outputs = self.model.generate(**inputs, max_length=150)
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            return response.strip()
        except Exception as e:
            logging.error(f"Error generating response: {e}")
            return "I'm having trouble generating a response. Please try again."

    def get_response(self, query: str, language: str = "English") -> Dict:
        """Process query and generate response."""
        try:
            is_emergency = self._check_emergency(query)
            if is_emergency:
                return {
                    "response": "IMPORTANT: If you're experiencing a medical emergency, please contact emergency services immediately.",
                    "is_emergency": True
                }
            
            relevant_info = self.knowledge_base.find_relevant_information(query)
            if relevant_info:
                return {
                    "response": relevant_info[0]['information'],
                    "is_emergency": False,
                    "relevant_info": relevant_info
                }
            
            prompt = f"You are a medical AI specializing in blood cancer.\nQuestion: {query}\nResponse:"
            response = self._generate_response(prompt)
            
            self.conversation_history.append({'role': 'user', 'content': query})
            self.conversation_history.append({'role': 'assistant', 'content': response})
            
            return {
                "response": response,
                "is_emergency": False,
                "relevant_info": relevant_info
            }
        except Exception as e:
            logging.error(f"Error processing query: {e}")
            return {
                "response": "I apologize, but I'm having trouble processing your query. Please try again.",
                "error": str(e)
            }
