from django.urls import path
from . import views
from rest_framework.routers import DefaultRouter

urlpatterns = [
    path('ai/', views.AIAssistantView.as_view()),
]

# router = DefaultRouter()
# router.register('orders', views.OrderViewSet)
# urlpatterns += router.urls