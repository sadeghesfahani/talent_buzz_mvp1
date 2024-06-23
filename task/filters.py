import django_filters

from .models import Task, TaskAssignment


class TaskFilter(django_filters.FilterSet):
    class Meta:
        model = Task
        fields = {
            'nectar': ['exact'],
        }

class TaskAssignmentFilter(django_filters.FilterSet):
    class Meta:
        model = TaskAssignment
        fields = {
            'task': ['exact'],
        }