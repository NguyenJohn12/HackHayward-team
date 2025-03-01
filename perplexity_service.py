import os
import requests
import json
import re
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional
import logging

load_dotenv()
logger = logging.getLogger(__name__)

class PerplexityService:
    def __init__(self):
        self.api_key = os.getenv("PERPLEXITY_API_KEY")
        self.api_url = "https://api.perplexity.ai"
        
        if not self.api_key:
            logger.warning("Perplexity API key not found in environment variables")
    
    def query_perplexity(self, query: str) -> Optional[str]:
        """Send a query to the Perplexity API using requests."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "sonar-pro",
            "messages": [
                {
                    "role": "user",
                    "content": query
                }
            ]
        }
        
        try:
            response = requests.post(
                f"{self.api_url}/chat/completions", 
                headers=headers, 
                json=payload
            )
            response.raise_for_status()
            
            # Extract the response text
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Error querying Perplexity API: {e}")
            return None
    
    def get_medication_recommendations(self, symptoms: List[str]) -> Optional[List[Dict[str, Any]]]:
        """Get medication recommendations based on symptoms and form type."""
        symptoms_text = ", ".join(symptoms)
        
        query = (
            f"I have the following symptoms: {symptoms_text}. "
            f"Please recommend exactly 3 over-the-counter medications "
            f"that would help, ranked by effectiveness (1st, 2nd, and 3rd choice). "
            f"For each medication, provide: 1) Brand name, 2) Active ingredients, "
            f"3) Recommended dosage, 4) Side effects"
            f"Format as a list with these details for each medication."
        )
        
        response_text = self.query_perplexity(query)
        if not response_text:
            return None
        
        return self.parse_medication_recommendations(response_text)
    
    def parse_medication_recommendations(self, response_text: str) -> List[Dict[str, Any]]:
        """Extract medication recommendations from Perplexity response."""
        medications = []
        
        try:
            # Split recommendations by rank
            medication_sections = re.split(r'(?:\n\s*\n|\n\s*(?:\d+(?:st|nd|rd|th)\s*choice|choice\s*\d+:))', response_text)
            medication_sections = [s for s in medication_sections if s.strip()]
            
            rank = 1
            for section in medication_sections[:3]:  # Process max 3 items
                if not section.strip():
                    continue
                
                medication_info = {
                    "rank": rank,
                    "name": None,
                    "active_ingredients": None,
                    "dosage": None,
                    "side_effects": None,
                }
                
                # Extract medication name
                name_patterns = [
                    r'(?:brand name|medication|name):\s*([^\n]+)',
                    r'^(?:\d+\.\s*)?([^:\n]+)(?::|$)'
                ]
                
                for pattern in name_patterns:
                    name_match = re.search(pattern, section, re.IGNORECASE | re.MULTILINE)
                    if name_match:
                        medication_info["name"] = name_match.group(1).strip()
                        break
                
                # Extract active ingredients
                ingredients_match = re.search(r'(?:active )?ingredients:\s*([^\n]+)', section, re.IGNORECASE)
                if ingredients_match:
                    medication_info["active_ingredients"] = ingredients_match.group(1).strip()
                
                # Extract dosage information
                dosage_match = re.search(r'(?:recommended )?dosage:\s*([^\n]+(?:\n\s+[^\n]+)*)', section, re.IGNORECASE)
                if dosage_match:
                    medication_info["dosage"] = dosage_match.group(1).strip()
                
                # Extract side effects
                side_effects_match = re.search(r'side effects:\s*([^\n]+(?:\n\s+[^\n]+)*)', section, re.IGNORECASE)
                if side_effects_match:
                    medication_info["side_effects"] = side_effects_match.group(1).strip()

                if medication_info["name"]:
                    medications.append(medication_info)
                    rank += 1
            
            return medications
            
        except Exception as e:
            logger.error(f"Error parsing medication recommendations: {e}")
            return []