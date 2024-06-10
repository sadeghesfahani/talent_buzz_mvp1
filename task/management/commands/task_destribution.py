from django.core.management import BaseCommand

from task.models import Task


class Command(BaseCommand):
    help = 'Check for tasks that need to be reassigned due to timeout'

    def handle(self, *args, **kwargs):
        active_tasks = Task.objects.filter(is_completed=False)
        for task in active_tasks:
            if task.is_searching_for_bees():
                task.assign_task()
                self.stdout.write(self.style.SUCCESS(f'Task {task.title} reassigned'))