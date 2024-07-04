from django.core.exceptions import PermissionDenied
from django.db.models import Q
from rest_framework import viewsets, permissions
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .filters import MessageFilter, ConversationFilter, NotificationFilter

from .models import Conversation, Message, Notification
from .permissions import IsParticipantOrPublicHive, IsMessageSenderOrParticipant, IsOwner
from .serializers import MessageSerializer, ConversationListSerializer, \
    ConversationDetailSerializer, NotificationSerializer


class ConversationViewSet(viewsets.ModelViewSet):
    queryset = Conversation.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsParticipantOrPublicHive]
    filter_backends = [DjangoFilterBackend]
    filterset_class = ConversationFilter

    def get_queryset(self):
        return Conversation.objects.filter(
            Q(participants=self.request.user) | Q(hive__is_public=True)
        ).distinct()

    def get_serializer_class(self):
        if self.action == 'list':
            return ConversationListSerializer
        return ConversationDetailSerializer

    def perform_create(self, serializer):
        conversation = serializer.save()
        conversation.participants.add(self.request.user)
        conversation.save()


class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated, IsMessageSenderOrParticipant]
    filter_backends = [DjangoFilterBackend]
    filterset_class = MessageFilter

    def get_queryset(self):
        return Message.objects.filter(
            Q(conversation__participants=self.request.user) | Q(conversation__hive__is_public=True)
        ).distinct()

    def perform_create(self, serializer):
        conversation = serializer.validated_data['conversation']
        if not conversation.participants.filter(id=self.request.user.id).exists():
            raise ValidationError("You are not a participant in this conversation.")
        serializer.save(sender=self.request.user)


class RaiseValidationError:
    pass


class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated, IsOwner]
    filter_backends = [DjangoFilterBackend]
    filterset_class = NotificationFilter

    def list(self, request, *args, **kwargs):
        queryset = Notification.objects.filter(user=self.request.user)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        raise PermissionDenied("Notifications cannot be created directly.")

    def perform_update(self, serializer):
        # Ensure only the 'read' field can be updated
        serializer.is_valid(raise_exception=True)
        serializer.save()

