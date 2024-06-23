from rest_framework.permissions import BasePermission

from honeycomb.models import Bee


class IsTaskOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        bee = Bee.objects.get(user=request.user)
        try:
            return obj.contract.bee == bee or obj.contract.hive.admins.filter(id=request.user.id).exists()
        except Exception as e:
            print(e)
            return False


class IsTaskAssignmentOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        bee = Bee.objects.get(user=request.user)
        return obj.bee == bee
