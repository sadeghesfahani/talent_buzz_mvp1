from django.db import models


# Create your models here.

class Usage(models.Model):
    user = models.ForeignKey('user.User', on_delete=models.CASCADE, related_name='user_usages')
    completion_tokens = models.IntegerField(default=0)
    prompt_tokens = models.IntegerField(default=0)
    duration = models.IntegerField(default=0)
    model = models.CharField(max_length=255, blank=True)
    run_id = models.CharField(max_length=255, blank=True)
    type = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        price_model = self.get_model_price()
        total_price = self.completion_tokens * price_model.output + self.prompt_tokens * price_model.prompt
        return self.user.first_name + " " + self.user.last_name + " - " + str(total_price) + "$"

    def get_model_price(self):
        return ModelPrice.objects.filter(model=self.model).first()


class ModelPrice(models.Model):
    model = models.CharField(max_length=255, blank=True)
    output = models.FloatField(default=0.0)
    prompt = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.model


class Instruction(models.Model):
    name = models.CharField(max_length=255, blank=True)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.text

class Assistant(models.Model):
    user = models.ForeignKey('user.User', on_delete=models.CASCADE, related_name='user_assistants')
    name = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
class Run(models.Model):
    thread = models.ForeignKey('assistant.UserThread', on_delete=models.CASCADE, related_name='thread_runs')
    assistant = models.ForeignKey('assistant.Assistant', on_delete=models.CASCADE, related_name='assistant_runs')
    status = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    model = models.CharField(max_length=255, blank=True)
    incomplete_details = models.TextField()
    metadata = models.JSONField(blank=True, null=True)
    response_format = models.CharField(max_length=255, blank=True)


class Message(models.Model):
    message_id = models.CharField(max_length=255, blank=True)
    text = models.TextField()
    user = models.ForeignKey('user.User', on_delete=models.CASCADE, related_name='user_messages')
    thread = models.ForeignKey('assistant.UserThread', on_delete=models.CASCADE, related_name='thread_messages')
    run = models.ForeignKey('assistant.Run', on_delete=models.CASCADE, related_name='run_messages')
    role = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.text

class UserThread(models.Model):
    user = models.ForeignKey('user.User', on_delete=models.CASCADE, related_name='user_threads')
    thread_id = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.first_name + " " + self.user.last_name + " - " + self.thread_id