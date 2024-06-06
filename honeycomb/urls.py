from django.urls import include, path
from rest_framework.routers import DefaultRouter
from . import views
from .views import MembershipAcceptView

router = DefaultRouter()
router.register(r'hives', views.HiveViewSet)
router.register(r'bees', views.BeeViewSet)
router.register(r'memberships', views.MembershipViewSet)
router.register(r'nectars', views.NectarViewSet)
router.register(r'hive-requests', views.HiveRequestViewSet)
router.register(r'contracts', views.ContractViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('accept_hive_membership', MembershipAcceptView.as_view()),
]
