from django.conf import settings
from django.db import models
from simple_history.models import HistoricalRecords

from communication.websocket_helper import WebSocketHelper


class Conversation(models.Model):
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='conversations')
    hive = models.ForeignKey('honeycomb.Hive', null=True, blank=True, on_delete=models.CASCADE,
                             related_name='hive_conversations')
    nectar = models.ForeignKey('honeycomb.Nectar', null=True, blank=True, on_delete=models.CASCADE,
                               related_name='nectar_conversations')
    tag = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    change_history = HistoricalRecords()

    def __str__(self):
        return f"Conversation {self.id}"

    def convert_to_ai_readable(self):
        return f"conversation with ID {self.id}, the number of participants in this conversation are {self.participants.all().count()} . this conversation is belong to {self.hive.convert_to_ai_readable() if self.hive else self.nectar.convert_to_ai_readable()}, the 3 messages in this conversation are {', '.join([message.convert_to_ai_readable() for message in self.messages.all()[:3]])} ."


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='sent_messages', on_delete=models.CASCADE)
    content = models.TextField()
    document = models.ForeignKey('common.Document', null=True, blank=True, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    change_history = HistoricalRecords()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        WebSocketHelper.send_message_to_conversation(self)

    def __str__(self):
        return f"Message from {self.sender} at {self.timestamp}"

    def convert_to_ai_readable(self):
        return f"message with ID {self.id}, the sender of this message is {self.sender}, the content of this message is {self.content} .{f' this message contains a document with this details: {self.document.convert_to_ai_readable()}' if self.document else ''}"


class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='notifications', on_delete=models.CASCADE)
    message = models.TextField()
    read = models.BooleanField(default=False)
    notification_type = models.CharField(max_length=100)
    notification_channel = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)
    change_history = HistoricalRecords()

    def read_notification(self):
        self.read = True
        self.save()
        return self

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.send_notification_via_ws()

    def __str__(self):
        return f"Notification for {self.user}"

    # send notification to ws channels
    def send_notification_via_ws(self):
        WebSocketHelper.send_notification(self.user, self.message)

    def convert_to_ai_readable(self):
        return f"{self.message} ."
