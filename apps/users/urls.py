from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.users.views import UserViewSet, ProfileViewSet, FarmDataListCreateView, FarmDataDetailView

router = DefaultRouter()
router.register(r'', UserViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
    path('profile/', ProfileViewSet.as_view({'get': 'list', 'put': 'update'}), name='profile'),
    path('farm-data/', FarmDataListCreateView.as_view(), name='farm-data-list'),
    path('farm-data/<int:pk>/', FarmDataDetailView.as_view(), name='farm-data-detail'),
]
