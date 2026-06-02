from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import ChatMessage, DiseaseDetection, YieldPrediction
from .serializers import ChatMessageSerializer, DiseaseDetectionSerializer, YieldPredictionSerializer
from .gemini_client import GeminiClient, HuggingFaceClient


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def chat_with_assistant(request):
    """Send message to farming assistant chatbot"""
    try:
        user_message = request.data.get('message')
        if not user_message:
            return Response({'error': 'Message is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        user_profile = request.user.profile
        
        # Get response from Gemini with real farm data context
        client = GeminiClient()
        assistant_message = client.get_farming_advice(user_message, user_profile=user_profile)
        
        if not assistant_message:
            return Response({'error': 'Could not get response from AI'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        # Save chat message
        chat = ChatMessage.objects.create(
            user_profile=user_profile,
            user_message=user_message,
            assistant_message=assistant_message
        )
        
        serializer = ChatMessageSerializer(chat)
        return Response(serializer.data)
    
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def detect_disease(request):
    """Detect crop disease from image"""
    try:
        image = request.FILES.get('image')
        if not image:
            return Response({'error': 'Image is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        user_profile = request.user.profile
        
        # Save image temporarily
        from django.core.files.storage import default_storage
        import os
        
        temp_path = f'temp_{user_profile.id}_{image.name}'
        path = default_storage.save(temp_path, image)
        full_path = default_storage.path(path)
        
        # Detect disease
        client = HuggingFaceClient()
        result = client.detect_crop_disease(full_path)
        
        # Clean up temp file
        default_storage.delete(path)
        
        if not result:
            return Response({'error': 'Could not process image'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        # Save detection result
        detection = DiseaseDetection.objects.create(
            user_profile=user_profile,
            image=image,
            disease_name=result['disease'],
            confidence=result['confidence'],
            treatment_suggestions=f"Detected: {result['disease']} with {result['confidence']:.0%} confidence. Please consult a local agricultural expert for treatment recommendations."
        )
        
        serializer = DiseaseDetectionSerializer(detection)
        return Response(serializer.data)
    
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def predict_yield(request):
    """Predict crop yield"""
    try:
        crop_type = request.data.get('crop_type')
        temperature = request.data.get('temperature')
        rainfall = request.data.get('rainfall')
        soil_nitrogen = request.data.get('soil_nitrogen')
        
        if not all([crop_type, temperature, rainfall, soil_nitrogen]):
            return Response({'error': 'All fields are required'}, status=status.HTTP_400_BAD_REQUEST)
        
        user_profile = request.user.profile
        
        # Get prediction
        client = HuggingFaceClient()
        result = client.predict_crop_yield(crop_type, float(temperature), float(rainfall), float(soil_nitrogen))
        
        if not result:
            return Response({'error': 'Could not generate prediction'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        # Save prediction
        prediction = YieldPrediction.objects.create(
            user_profile=user_profile,
            crop_name=crop_type,
            expected_yield_per_hectare=result['predicted_yield'],
            confidence=result['confidence'],
            factors_considered=result['factors']
        )
        
        serializer = YieldPredictionSerializer(prediction)
        return Response(serializer.data)
    
    except ValueError as e:
        return Response({'error': 'Invalid numeric values'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ChatHistoryListView(generics.ListAPIView):
    """Get chat history for current user"""
    permission_classes = [IsAuthenticated]
    serializer_class = ChatMessageSerializer
    
    def get_queryset(self):
        return ChatMessage.objects.filter(user_profile=self.request.user.profile).order_by('-created_at')


class DiseaseDetectionListView(generics.ListAPIView):
    """Get disease detection history"""
    permission_classes = [IsAuthenticated]
    serializer_class = DiseaseDetectionSerializer
    
    def get_queryset(self):
        return DiseaseDetection.objects.filter(user_profile=self.request.user.profile).order_by('-created_at')


class YieldPredictionListView(generics.ListAPIView):
    """Get yield prediction history"""
    permission_classes = [IsAuthenticated]
    serializer_class = YieldPredictionSerializer
    
    def get_queryset(self):
        return YieldPrediction.objects.filter(user_profile=self.request.user.profile).order_by('-created_at')
