from rest_framework.permissions import BasePermission

from honeycomb.models import Bee, Contract


class IsTaskOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        bee = Bee.objects.get(user=request.user)
        has_permission = False
        try:
            has_permission = obj.contract.bee == bee
        except Exception as e:
            has_permission = False

        if not has_permission:

            try:
                has_permission = obj.nectar.nectar_hive.admins.filter(id=request.user.id).exists()
            except Exception as e:
                has_permission = False

        return has_permission


class IsTaskAssignmentOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        bee = Bee.objects.get(user=request.user)
        return obj.bee == bee
