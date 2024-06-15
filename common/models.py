from django.conf import settings
from django.db import models
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from openai import OpenAI

client = OpenAI(api_key=settings.OPEN_AI_API_KEY)
# Create your models here.
class Document(models.Model):
    user = models.ForeignKey('user.User', on_delete=models.CASCADE)
    document = models.FileField(upload_to='documents')
    file_id = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.personal_details.first_name + " " + self.user.personal_details.last_name + " - " + self.document.name

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        if not self.file_id:
            uploaded_file = client.files.create(
                file=(self.document.file.name,self.document.file.open('rb').read()), purpose="assistants"
            )
            self.file_id = uploaded_file.id
        super().save(force_insert, force_update, using, update_fields)


@receiver(post_save, sender=Document)
def set_file_id(sender, instance, **kwargs):
    if settings.IS_TEST:
        return  # Skip signal handling during tests
    if not instance.file_id and instance.document:
        uploaded_file = client.files.create(
            file=(instance.document.file.name, instance.document.file.open('rb').read()), purpose="assistants"
        )
        instance.file_id = uploaded_file.id
class Photo(models.Model):
    user = models.ForeignKey('user.User', on_delete=models.CASCADE)
    photo = models.ImageField(upload_to='photos')
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.first_name + " " + self.user.last_name + " - " + self.photo.name