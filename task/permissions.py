from django.core.exceptions import ObjectDoesNotExist
from rest_framework.permissions import BasePermission

from honeycomb.models import Bee


class IsTaskOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        bee = Bee.objects.get(user=request.user)
        return True
        # try:
        #     return obj.contract.bee == bee
        # except ObjectDoesNotExist:
        #     return None



class IsTaskAssignmentOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        bee = Bee.objects.get(user=request.user)
        return obj.bee == bee
