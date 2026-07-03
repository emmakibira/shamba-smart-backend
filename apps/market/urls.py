from django.urls import path
from .views import MarketPriceUploadView, MarketPriceListView

urlpatterns = [
    path('upload-pdf/', MarketPriceUploadView.as_view(), name='market-upload-pdf'),
    path('prices/', MarketPriceListView.as_view(), name='market-prices'),
]
