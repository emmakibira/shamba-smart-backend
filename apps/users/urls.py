from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.users.views import UserViewSet, ProfileViewSet

router = DefaultRouter()
router.register(r'', UserViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
    path('profile/', ProfileViewSet.as_view({'get': 'list', 'put': 'update'}), name='profile'),
]
