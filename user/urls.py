from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import UserViewSet, SkillViewSet, CertificateViewSet, PortfolioViewSet, EducationViewSet, ExperienceViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'skills', SkillViewSet)
router.register(r'certificates',  CertificateViewSet)
router.register(r'portfolio',  PortfolioViewSet)
router.register(r'education',  EducationViewSet)
router.register(r'experience',  ExperienceViewSet)

urlpatterns = [
    path('', include(router.urls))
]
