from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.crops.views import CropViewSet, CropRecommendationViewSet

router = DefaultRouter()
router.register(r'crops', CropViewSet, basename='crop')
router.register(r'recommendations', CropRecommendationViewSet, basename='recommendation')

urlpatterns = [
    path('', include(router.urls)),
]
