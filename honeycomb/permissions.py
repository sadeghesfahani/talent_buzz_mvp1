from rest_framework.permissions import BasePermission


class IsHiveAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user in obj.hive.admins.all()
