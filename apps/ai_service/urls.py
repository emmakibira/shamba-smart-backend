from django.urls import path
from .views import (
    chat_with_assistant,
    detect_disease,
    predict_yield,
    ChatHistoryListView,
    DiseaseDetectionListView,
    YieldPredictionListView
)

urlpatterns = [
    path('chat/', chat_with_assistant, name='chat'),
    path('chat-history/', ChatHistoryListView.as_view(), name='chat-history'),
    path('detect-disease/', detect_disease, name='detect-disease'),
    path('disease-history/', DiseaseDetectionListView.as_view(), name='disease-history'),
    path('predict-yield/', predict_yield, name='predict-yield'),
    path('yield-history/', YieldPredictionListView.as_view(), name='yield-history'),
]
