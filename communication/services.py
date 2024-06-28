


class NotificationService:

    @staticmethod
    def get_unread_notifications_AI_readable(user):
        from communication.models import Notification
        return " ,".join([notification.read_notification().convert_to_ai_readable() for notification in Notification.objects.filter(user=user, read=False)])


class ConversationService:

    @staticmethod
    def get_conversations_AI_readable(user):
        from communication.models import Conversation
        return [conversation.convert_to_ai_readable() for conversation in Conversation.objects.filter(participants=user)]

