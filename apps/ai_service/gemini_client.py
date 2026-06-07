import google.generativeai as genai
import requests
import logging
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)


class GeminiClient:
    """Client for Google Gemini API with real farm data context"""
    
    def __init__(self):
        self.api_key = getattr(settings, 'GEMINI_API_KEY', '')
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-pro')
        else:
            self.model = None
    
    def get_real_farm_context(self, user_profile):
        """Build comprehensive context from real farm data"""
        context_parts = []
        
        # User's farm info
        context_parts.append(f"Farm size: {user_profile.farm_size} hectares")
        context_parts.append(f"Soil type: {user_profile.soil_type}")
        
        # Current crops
        crops = user_profile.get_crops_list()
        if crops:
            context_parts.append(f"Current crops: {', '.join(crops)}")
        
        # Real-time sensor data
        from apps.farm_data.models import SensorDevice, SensorReading
        from apps.farm_data.services import WeatherService
        
        sensors = SensorDevice.objects.filter(user=user_profile.user, status='active')
        if sensors.exists():
            context_parts.append("Real-time sensor data:")
            for sensor in sensors:
                latest = sensor.readings.latest('timestamp') if sensor.readings.exists() else None
                if latest:
                    context_parts.append(
                        f"  - {sensor.name}: {latest.value} {sensor.unit} (last updated {latest.timestamp.strftime('%H:%M')})"
                    )
        
        # Current weather
        if user_profile.latitude and user_profile.longitude:
            weather = WeatherService.get_weather(user_profile.latitude, user_profile.longitude)
            if weather:
                temp = weather.get('main', {}).get('temp')
                humidity = weather.get('main', {}).get('humidity')
                weather_desc = weather.get('weather', [{}])[0].get('description', 'unknown')
                context_parts.append(
                    f"Current weather: {weather_desc}, {temp}°C, {humidity}% humidity"
                )
            
            # Weather forecast
            forecast = WeatherService.get_weather_forecast(
                user_profile.latitude, 
                user_profile.longitude, 
                days=3
            )
            if forecast:
                context_parts.append("3-day forecast:")
                for day in forecast[:3]:
                    context_parts.append(
                        f"  - {day['date']}: {day['description']}, {day['temp_min']}°C-{day['temp_max']}°C"
                    )
        
        # Recent farm activities
        from apps.farm_data.models import SensorAlert
        recent_alerts = SensorAlert.objects.filter(
            sensor__user=user_profile.user,
            is_resolved=False
        ).order_by('-created_at')[:3]
        
        if recent_alerts.exists():
            context_parts.append("Active alerts:")
            for alert in recent_alerts:
                context_parts.append(f"  - {alert.message} (Severity: {alert.severity})")
        
        return "\n".join(context_parts)
    
    def get_farming_advice(self, user_message, user_profile=None, context=None):
        """Get farming advice from Gemini with real data context"""
        if not self.model:
            logger.error("Gemini API not configured")
            return "AI service is not available. Please contact support."
        
        try:
            system_prompt = """You are an expert agricultural advisor with deep knowledge of:
            - Crop management and best practices
            - Pest and disease control strategies
            - Soil management and fertilization
            - Weather-based farming decisions
            - Water management and irrigation
            - Sustainable farming practices
            
            Provide practical, actionable advice based on the farmer's real farm data.
            Be specific and reference the actual conditions when possible.
            Prioritize sustainable and cost-effective solutions.
            Keep responses concise but informative."""
            
            # Get comprehensive context if user_profile provided
            if user_profile:
                real_context = self.get_real_farm_context(user_profile)
                system_prompt += f"\n\nFarmer's current situation:\n{real_context}"
            elif context:
                system_prompt += f"\n\nFarm context: {context}"
            
            full_message = f"{system_prompt}\n\nFarmer's question: {user_message}"
            
            response = self.model.generate_content(full_message)
            return response.text
        
        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}")
            return "Unable to get advice at this moment. Please try again later."




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
