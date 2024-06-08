from django.conf import settings
from django.db import models
from simple_history.models import HistoricalRecords


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


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='sent_messages', on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    change_history = HistoricalRecords()

    def __str__(self):
        return f"Message from {self.sender} at {self.timestamp}"


class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='notifications', on_delete=models.CASCADE)
    message = models.TextField()
    read = models.BooleanField(default=False)
    notification_type = models.CharField(max_length=100)
    notification_channel = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)
    change_history = HistoricalRecords()

    def __str__(self):
        return f"Notification for {self.user}"
