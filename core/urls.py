from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.http import HttpResponse
from rest_framework.routers import DefaultRouter
from apps.auth.views import AuthViewSet

# Add this function
def home_view(request):
    return HttpResponse(
        "<h1>Shamba Smart Backend API</h1>"
        "<p>Server is running</p>"
        "<p>Available endpoints:</p>"
        "<ul>"
        "<li>/api/auth/</li>"
        "<li>/api/users/</li>"
        "<li>/api/crops/</li>"
        "<li>/api/dashboard/</li>"
        "<li>/api/community/</li>"
        "<li>/api/market/</li>"
        "<li>/api/ai/</li>"
        "<li>/api/farm/</li>"
        "<li>/admin/</li>"
        "</ul>"
    )

router = DefaultRouter()
router.register(r'auth', AuthViewSet, basename='auth')

urlpatterns = [
    path('', home_view, name='root'),  # Add this line
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/auth/', include('apps.auth.urls')),
    path('api/users/', include('apps.users.urls')),
    path('api/crops/', include('apps.crops.urls')),
    path('api/dashboard/', include('apps.dashboard.urls')),
    path('api/community/', include('apps.community.urls')),
    path('api/market/', include('apps.market.urls')),
    path('api/ai/', include('apps.ai_service.urls')),
    path('api/farm/', include('apps.farm_data.urls')),
]

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)