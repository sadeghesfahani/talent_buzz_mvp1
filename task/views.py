from django.core.exceptions import ValidationError
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from honeycomb.models import Bee
from task.models import Task, TaskAssignment
from task.permissions import IsTaskOwner, IsTaskAssignmentOwner
from task.serializers import TaskSerializer, TaskAssignmentSerializer, CreateTaskAssignmentSerializer
from .filters import TaskFilter, TaskAssignmentFilter


# Create your views here.
class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated, IsTaskOwner]
    filter_backends = [DjangoFilterBackend]
    filterset_class = TaskFilter

    # def get_queryset(self):
    #     bee = Bee.objects.get(user=self.request.user)
    #     return Task.objects.filter(contract__bee=bee)


class TaskAssignmentViewSet(viewsets.ModelViewSet):
    queryset = TaskAssignment.objects.all()
    permission_classes = [IsAuthenticated, IsTaskAssignmentOwner]
    filter_backends = [DjangoFilterBackend]
    filterset_class = TaskAssignmentFilter

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateTaskAssignmentSerializer
        else:
            return TaskAssignmentSerializer

    # def get_queryset(self):
    #     bee = Bee.objects.get(user=self.request.user)
    #     return TaskAssignment.objects.filter(bee=bee)

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated, IsTaskAssignmentOwner])
    def accept(self, request, pk=None):
        assignment = self.get_object()
        try:
            assignment.accept()
            return Response({'status': 'success', 'assignment_id': assignment.id}, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response({'status': 'error', 'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)