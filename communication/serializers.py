from rest_framework import serializers

from .models import Conversation, Message, Notification


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


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'
        read_only_fields = ['id', 'user', 'message', 'notification_type', 'created_at']

    def update(self, instance, validated_data):
        # Update only the 'read' field
        for field in validated_data:
            if field == 'read':
                setattr(instance, field, validated_data[field])
        instance.save()
        return instance
