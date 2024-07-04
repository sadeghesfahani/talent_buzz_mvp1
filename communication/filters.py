import django_filters

from .models import Conversation, Message, Notification


class ConversationFilter(django_filters.FilterSet):
    class Meta:
        model = Conversation
        fields = {
            'nectar': ['exact'],
            'hive': ['exact'],
        }


class MessageFilter(django_filters.FilterSet):
    class Meta:
        model = Message
        fields = {
            'conversation': ['exact']
        }

class NotificationFilter(django_filters.FilterSet):
    class Meta:
        model = Notification
        fields = {
            'user': ['exact']
        }