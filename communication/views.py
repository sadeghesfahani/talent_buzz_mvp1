from django.db.models import Q
from rest_framework import viewsets, permissions
from rest_framework.exceptions import ValidationError

from .models import Conversation, Message
from .permissions import IsParticipantOrPublicHive, IsMessageSenderOrParticipant
from .serializers import MessageSerializer, ConversationListSerializer, \
    ConversationDetailSerializer


class ConversationViewSet(viewsets.ModelViewSet):
    queryset = Conversation.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsParticipantOrPublicHive]

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

    def get_queryset(self):
        return Message.objects.filter(
            Q(conversation__participants=self.request.user) | Q(conversation__hive__is_public=True)
        ).distinct()

    def perform_create(self, serializer):
        conversation = serializer.validated_data['conversation']
        if not conversation.participants.filter(id=self.request.user.id).exists():
            raise ValidationError("You are not a participant in this conversation.")
        serializer.save(sender=self.request.user)
