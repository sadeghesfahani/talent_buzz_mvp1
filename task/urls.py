from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TaskViewSet, TaskAssignmentViewSet

router = DefaultRouter()

router.register(r'tasks', TaskViewSet)
router.register(r'task-assignments', TaskAssignmentViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
