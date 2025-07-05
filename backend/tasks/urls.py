from django.urls import path
from . import views
from rest_framework.routers import DefaultRouter
from rest_framework.routers import DefaultRouter

urlpatterns = [
    path('ai/', views.AIAssistantView.as_view()),

]
router = DefaultRouter()
router.register(r'boards', views.BoardViewSet,)
router.register(r'columns', views.ColumnViewSet,)
router.register(r'tasks', views.TaskViewSet,)
router.register(r'subtasks', views.SubtaskViewSet,)
urlpatterns += router.urls
