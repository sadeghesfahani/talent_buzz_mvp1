from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import UserViewSet, SkillViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'skills', SkillViewSet)

urlpatterns = [
    path('', include(router.urls))
]
