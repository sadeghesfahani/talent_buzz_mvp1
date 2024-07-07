from django.core.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from honeycomb.models import Bee
from task.filters import TaskAssignmentFilter, TaskFilter
from task.models import Task, TaskAssignment
from task.permissions import IsTaskOwner, IsTaskAssignmentOwner
from task.serializers import TaskSerializer, CreateTaskSerializer, TaskAssignmentSerializer, CreateTaskAssignmentSerializer


# Create your views here.
class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_class = TaskFilter
    permission_classes = [IsAuthenticated, IsTaskOwner]

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update' or self.action == 'partial_update':
            return CreateTaskSerializer
        else:
            return TaskSerializer




class TaskAssignmentViewSet(viewsets.ModelViewSet):
    queryset = TaskAssignment.objects.all()
    permission_classes = [IsAuthenticated, IsTaskAssignmentOwner]
    filter_backends = [DjangoFilterBackend]
    filterset_class = TaskAssignmentFilter

    # def get_queryset(self):
    #     bee = Bee.objects.get(user=self.request.user)
    #     return TaskAssignment.objects.filter(bee=bee)

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateTaskAssignmentSerializer
        else:
            return TaskAssignmentSerializer
#
#
#     @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated, IsTaskAssignmentOwner])
#     def accept(self, request, pk=None):
#         assignment = self.get_object()
#         try:
#             assignment.accept()
#             return Response({'status': 'success', 'assignment_id': assignment.id}, status=status.HTTP_200_OK)
#         except ValidationError as e:
#             return Response({'status': 'error', 'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)