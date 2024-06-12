from django.db import models


# Create your models here.
class HiveThread(models.Model):
    hive = models.ForeignKey('honeycomb.Hive', on_delete=models.CASCADE)
    vector_store = models.CharField(max_length=255, blank=True)
    user = models.ForeignKey('user.User', on_delete=models.CASCADE)
    thread_id = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Thread {self.id}"
