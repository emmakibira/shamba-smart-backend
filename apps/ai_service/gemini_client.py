import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class GeminiClient:
    """Client for Google Gemini API using the new google-genai SDK"""

    def __init__(self):
        self.api_key = getattr(settings, 'GEMINI_API_KEY', '')
        self.client = None
        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
            except ImportError:
                logger.error("google-genai package not installed. Run: pip install google-genai")

    def get_real_farm_context(self, user_profile):
        """Build comprehensive context from real farm data"""
        context_parts = []
        context_parts.append(f"Farm size: {user_profile.farm_size} hectares")
        context_parts.append(f"Soil type: {user_profile.soil_type}")

        crops = user_profile.get_crops_list()
        if crops:
            context_parts.append(f"Current crops: {', '.join(crops)}")

        from apps.farm_data.models import SensorDevice
        from apps.farm_data.services import WeatherService

        sensors = SensorDevice.objects.filter(user=user_profile.user, status='active')
        if sensors.exists():
            context_parts.append("Real-time sensor data:")
            for sensor in sensors:
                latest = sensor.readings.latest('timestamp') if sensor.readings.exists() else None
                if latest:
                    context_parts.append(
                        f"  - {sensor.name}: {latest.value} {sensor.unit} "
                        f"(last updated {latest.timestamp.strftime('%H:%M')})"
                    )

        if user_profile.latitude and user_profile.longitude:
            weather = WeatherService.get_weather(user_profile.latitude, user_profile.longitude)
            if weather:
                current = weather.get('current_weather', {})
                temp = current.get('temperature', 'N/A')
                wind = current.get('windspeed', 'N/A')
                context_parts.append(f"Current weather: {temp}°C, wind {wind} km/h")

        return "\n".join(context_parts)

    def get_farming_advice(self, user_message, user_profile=None, context=None):
        """Get farming advice from Gemini"""
        if not self.client:
            logger.error("Gemini client not configured")
            return "AI service is not available. Please contact support."

        try:
            system_prompt = (
                "You are an expert agricultural advisor for small-scale Tanzanian farmers. "
                "Provide practical, actionable advice based on local conditions. "
                "Be specific, concise, and reference actual sensor/weather data when provided. "
                "Prioritise sustainable and affordable solutions."
            )

            if user_profile:
                farm_context = self.get_real_farm_context(user_profile)
                system_prompt += f"\n\nFarmer's current situation:\n{farm_context}"
            elif context:
                system_prompt += f"\n\nFarm context: {context}"

            full_prompt = f"{system_prompt}\n\nFarmer's question: {user_message}"

            from google import genai
            response = self.client.models.generate_content(
                model='gemini-2.0-flash',
                contents=full_prompt,
            )
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
            if isinstance(results, list) and results:
                top_result = max(results, key=lambda x: x.get('score', 0))
                return {
                    'disease': top_result.get('label', 'Unknown Disease'),
                    'confidence': top_result.get('score', 0),
                    'all_results': results
                }
            return None

        except Exception as e:
            logger.error(f"HuggingFace API error: {str(e)}")
            return None

    def predict_crop_yield(self, crop_type, temperature, rainfall, soil_nitrogen):
        """Predict crop yield based on parameters"""
        try:
            base_yields = {
                'rice': 5000, 'wheat': 5500, 'maize': 5000,
                'potato': 20000, 'sugarcane': 65000, 'cotton': 1500,
                'groundnut': 1500, 'soybean': 1800,
            }
            base_yield = base_yields.get(crop_type.lower(), 3000)

            temp_factor = 1.0 if 15 <= temperature <= 25 else (0.95 if temperature <= 30 else 0.85)
            rainfall_factor = 1.0 if 500 <= rainfall <= 1500 else (0.7 if rainfall < 500 else 0.95)
            soil_factor = 1.0 if soil_nitrogen >= 200 else (0.9 if soil_nitrogen >= 150 else 0.75)

            predicted_yield = base_yield * temp_factor * rainfall_factor * soil_factor

            return {
                'crop': crop_type,
                'predicted_yield': round(predicted_yield, 2),
                'unit': 'kg/hectare',
                'confidence': 0.6,
                'factors': {
                    'temperature': temperature,
                    'rainfall': rainfall,
                    'soil_nitrogen': soil_nitrogen,
                }
            }

        except Exception as e:
            logger.error(f"Yield prediction error: {str(e)}")
            return None