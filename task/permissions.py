from rest_framework.permissions import BasePermission

from honeycomb.models import Bee


class IsTaskOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        bee = Bee.objects.get(user=request.user)
        return obj.contract.bee == bee


class IsTaskAssignmentOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        bee = Bee.objects.get(user=request.user)
        return obj.bee == bee
