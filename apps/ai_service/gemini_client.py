import google.generativeai as genai
import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class GeminiClient:
    """Client for Google Gemini API"""
    
    def __init__(self):
        self.api_key = getattr(settings, 'GEMINI_API_KEY', '')
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-pro')
    
    def get_farming_advice(self, user_message, context=None):
        """Get farming advice from Gemini"""
        try:
            system_prompt = """You are an expert agricultural advisor with deep knowledge of farming practices, crop management, pest control, and soil management. 
            Provide practical, actionable advice for farmers. Be specific and reference local/regional practices when possible.
            Keep responses concise but informative."""
            
            if context:
                system_prompt += f"\nUser's farm context: {context}"
            
            full_message = f"{system_prompt}\n\nUser question: {user_message}"
            
            response = self.model.generate_content(full_message)
            return response.text
        
        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}")
            return None


class HuggingFaceClient:
    """Client for Hugging Face Inference API"""
    
    def __init__(self):
        self.api_key = getattr(settings, 'HUGGINGFACE_API_KEY', '')
        self.base_url = "https://api-inference.huggingface.co/models"
    
    def detect_crop_disease(self, image_path):
        """Detect crop diseases from image"""
        try:
            # Using ResNet50 for disease detection
            model_id = "microsoft/resnet-50"
            headers = {"Authorization": f"Bearer {self.api_key}"}
            
            with open(image_path, "rb") as f:
                data = f.read()
            
            response = requests.post(
                f"{self.base_url}/{model_id}",
                headers=headers,
                data=data,
                timeout=30
            )
            
            if response.status_code != 200:
                logger.error(f"HF API error: {response.text}")
                return None
            
            results = response.json()
            
            # Process results to identify disease
            if isinstance(results, list):
                # Get top result
                top_result = max(results, key=lambda x: x.get('score', 0))
                disease_name = top_result.get('label', 'Unknown Disease')
                confidence = top_result.get('score', 0)
                
                return {
                    'disease': disease_name,
                    'confidence': confidence,
                    'all_results': results
                }
            
            return None
        
        except Exception as e:
            logger.error(f"HuggingFace API error: {str(e)}")
            return None
    
    def predict_crop_yield(self, crop_type, temperature, rainfall, soil_nitrogen):
        """Predict crop yield based on parameters (simplified)"""
        try:
            # This is a simplified prediction - in production, use more complex models
            # Base yields by crop (kg/hectare)
            base_yields = {
                'rice': 5000,
                'wheat': 5500,
                'maize': 5000,
                'potato': 20000,
                'sugarcane': 65000,
                'cotton': 1500,
                'groundnut': 1500,
                'soybean': 1800,
            }
            
            base_yield = base_yields.get(crop_type.lower(), 3000)
            
            # Adjust based on conditions
            # Temperature adjustment
            if 15 <= temperature <= 25:
                temp_factor = 1.0
            elif 25 < temperature <= 30:
                temp_factor = 0.95
            else:
                temp_factor = 0.85
            
            # Rainfall adjustment
            if 500 <= rainfall <= 1500:
                rainfall_factor = 1.0
            elif rainfall < 500:
                rainfall_factor = 0.7
            else:
                rainfall_factor = 0.95
            
            # Soil nutrition
            if soil_nitrogen >= 200:
                soil_factor = 1.0
            elif soil_nitrogen >= 150:
                soil_factor = 0.9
            else:
                soil_factor = 0.75
            
            predicted_yield = base_yield * temp_factor * rainfall_factor * soil_factor
            confidence = 0.6  # Simplified confidence
            
            return {
                'crop': crop_type,
                'predicted_yield': round(predicted_yield, 2),
                'unit': 'kg/hectare',
                'confidence': confidence,
                'factors': {
                    'temperature': temperature,
                    'rainfall': rainfall,
                    'soil_nitrogen': soil_nitrogen
                }
            }
        
        except Exception as e:
            logger.error(f"Yield prediction error: {str(e)}")
            return None
