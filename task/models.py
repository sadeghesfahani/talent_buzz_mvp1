from django.db import models
from django.db.models.functions import datetime
from simple_history.models import HistoricalRecords



class BeeSelection(models.Model):
    bees = models.ManyToManyField("honeycomb.Bee", related_name='selected_for', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    removed_bees = models.ManyToManyField("honeycomb.Bee", related_name='removed_from_selection', blank=True)
    history = HistoricalRecords()

    def add_bee(self, bee: 'Bee'):
        self.bees.add(bee)
        self.save()

    def remove_bee(self, bee: 'Bee'):
        self.bees.remove(bee)
        self.removed_bees.add(bee)
        self.save()


# Create your models here.
class Task(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    contract = models.ForeignKey('honeycomb.Contract', on_delete=models.CASCADE, related_name='tasks')
    assigned_bees = models.ManyToManyField('honeycomb.Bee', related_name='tasks', blank=True)
    bee_selection = models.OneToOneField('BeeSelection', on_delete=models.CASCADE, related_name='task',
                                         null=True, blank=True)
    reports = models.ManyToManyField('honeycomb.Report', related_name='tasks', blank=True)
    required_number_of_bees = models.IntegerField(default=1)  # Number of bees required for the task
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    due_date = models.DateTimeField(null=True, blank=True)
    priority = models.IntegerField(default=1)
    urgency = models.IntegerField(default=1)
    status = models.CharField(max_length=255, default='pending')
    documents = models.ManyToManyField('common.Document', related_name='tasks', blank=True)
    change_history = HistoricalRecords()

    def __str__(self):
        return self.title

    def is_searching_for_bees(self):
        return self.required_number_of_bees > self.assigned_bees.count()

    def assign_task(self):
        self.pending_assignments.all().delete()
        reasonable_invitation_number = 5 * self.required_number_of_bees
        for bee in self.bee_selection.bees.all():

            TaskAssignment.objects.create(task=self, bee=bee)
            self.bee_selection.remove_bee(bee)
            if self.assigned_bees.count() == reasonable_invitation_number:
                break


class TaskAssignment(models.Model):
    task = models.ForeignKey('Task', on_delete=models.CASCADE, related_name='pending_assignments')
    bee = models.ForeignKey('honeycomb.Bee', on_delete=models.CASCADE, related_name='pending_task_assignments')
    assigned_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    is_accepted = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)
    change_history = HistoricalRecords()

    def accept(self):
        if self.is_active and not self.is_accepted:
            self.is_accepted = True
            self.is_active = False
            self.accepted_at = datetime.datetime.now()
            self.task.assigned_bees.add(self.bee)
            self.save()
            self.task.save()

            if not self.task.is_searching_for_bees():
                TaskAssignment.objects.filter(task=self.task, is_accepted=False).delete()

    def __str__(self):
        return f"{self.bee} -> {self.task}"
