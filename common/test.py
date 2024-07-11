from django.db import models


class Quest(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    reward = models.IntegerField()
    def __str__(self):
        return self.name

class QuestProgress(models.Model):
    quest = models.ForeignKey(Quest, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    def __str__(self):
        return f'{self.user.username} - {self.quest.name}'
