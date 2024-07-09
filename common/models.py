import hashlib

from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from openai import OpenAI

client = OpenAI(api_key=settings.OPEN_AI_API_KEY)


# Create your models here.
class Document(models.Model):
    user = models.ForeignKey('user.User', on_delete=models.CASCADE, related_name='user_documents')
    document = models.FileField(upload_to='documents')
    file_id = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    purpose = models.CharField(max_length=255, blank=True)
    isolated_vector_store = models.CharField(max_length=255, blank=True)
    hash = models.CharField(max_length=255, unique=True, blank=True)
    is_ai_sync = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.personal_details.first_name + " " + self.user.personal_details.last_name + " - " + self.document.name

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):

        if self.document:  # Check if there is a document to process
            file_hash = self.calculate_hash(self.document)  # Calculate hash
            existing_document = Document.objects.filter(hash=file_hash).first()
            if existing_document:
                # If an existing document is found, point the current instance to it
                self.id = existing_document.id  # Set the current object's ID to the existing one
                self.document = existing_document.document  # Re-use the existing document file
                self.file_id = existing_document.file_id  # Re-use the existing file_id
                if update_fields:
                    # Only update fields that are explicitly listed
                    super().save(force_insert, force_update, using, update_fields)
                return
            else:
                self.hash = file_hash  # Set the new hash if no document is found

        if self.is_ai_sync and not self.file_id:
            # Upload file and set file_id only if it's a new file and no existing document was found
            uploaded_file = client.files.create(
                file=(self.document.file.name, self.document.file.open('rb').read()), purpose="assistants"
            )
            self.file_id = uploaded_file.id

            # Proceed with saving as a new document
        super().save(force_insert, force_update, using, update_fields)

    def convert_to_ai_readable(self):
        return f"""
        representetive file_id in vectore store is : {self.file_id}, user document description is : {self.description}
        """

    @staticmethod
    def calculate_hash(file_field):
        """
        Calculate MD5 hash of a file.
        """
        md5_hash = hashlib.md5()
        for chunk in file_field.chunks():
            md5_hash.update(chunk)
        return md5_hash.hexdigest()


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
