from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.dashboard.views import WeatherViewSet, AlertViewSet, DashboardViewSet

router = DefaultRouter()
router.register(r'weather', WeatherViewSet, basename='weather')
router.register(r'alerts', AlertViewSet, basename='alert')
router.register(r'dashboard', DashboardViewSet, basename='dashboard-overview')

urlpatterns = [
    path('', include(router.urls)),
    path('overview/', DashboardViewSet.as_view({'get': 'overview'}), name='dashboard-overview'),
]
