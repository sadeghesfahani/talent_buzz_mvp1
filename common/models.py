from django.db import models


# Create your models here.
class Document(models.Model):
    user = models.ForeignKey('user.User', on_delete=models.CASCADE)
    document = models.FileField(upload_to='documents')
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.personal_details.first_name + " " + self.user.personal_details.last_name + " - " + self.document.name

class Photo(models.Model):
    user = models.ForeignKey('user.User', on_delete=models.CASCADE)
    photo = models.ImageField(upload_to='photos')
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.first_name + " " + self.user.last_name + " - " + self.photo.name