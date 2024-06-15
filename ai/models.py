from django.db import models


# Create your models here


class AssistantInfo(models.Model):
    general_assistant_id = models.CharField(max_length=255, blank=True)
    hive_assistant_id = models.CharField(max_length=255, blank=True)
    backend_assistant_id = models.CharField(max_length=255, blank=True)
    base_vector_store_id = models.CharField(max_length=255, blank=True)



class Thread(models.Model):
    user = models.ForeignKey('user.User', on_delete=models.CASCADE, related_name='threads')
    thread_id = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now=True)
    title = models.CharField(max_length=255, blank=True)


class Message(models.Model):
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name='messages')
    user = models.ForeignKey('user.User', on_delete=models.CASCADE)
    content = models.TextField()
    response = models.TextField(blank=True)
    status = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
