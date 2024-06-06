from rest_framework import serializers

from .models import Conversation, Message


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = '__all__'


class ConversationListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = "__all__"


class ConversationDetailSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = "__all__"
