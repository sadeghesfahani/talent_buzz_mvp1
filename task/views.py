from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from honeycomb.models import Bee
from task.models import Task, TaskAssignment
from task.permissions import IsTaskOwner, IsTaskAssignmentOwner
from task.serializers import TaskSerializer, TaskAssignmentSerializer


# Create your views here.
class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated, IsTaskOwner]

    def get_queryset(self):
        bee = Bee.objects.get(user=self.request.user)
        return Task.objects.filter(contract__bee=bee)


class TaskAssignmentViewSet(viewsets.ModelViewSet):
    queryset = TaskAssignment.objects.all()
    serializer_class = TaskAssignmentSerializer
    permission_classes = [IsAuthenticated, IsTaskAssignmentOwner]

    def get_queryset(self):
        bee = Bee.objects.get(user=self.request.user)
        return TaskAssignment.objects.filter(bee=bee)
