# chat/permissions.py
from rest_framework import permissions


class IsParticipantOrPublicHive(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # Allow access if the user is a participant of the conversation
        if request.user in obj.participants.all():
            return True
        # Allow access if the conversation is part of a public hive
        if obj.hive and obj.hive.is_public:
            return True
        return False


class IsMessageSenderOrParticipant(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # Check if the user is the sender of the message or a participant in the conversation
        return request.user == obj.sender or request.user in obj.conversation.participants.all()
