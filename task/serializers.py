from rest_framework import serializers
from honeycomb.serializers import ContractSerializer, BeeWithDetailSerializer
from task.models import Task, TaskAssignment


class TaskSerializer(serializers.ModelSerializer):
    contract = ContractSerializer(read_only=True)

    class Meta:
        model = Task
        fields = '__all__'


class TaskAssignmentSerializer(serializers.ModelSerializer):
    bee = BeeWithDetailSerializer(read_only=True)
    class Meta:
        model = TaskAssignment
        fields = '__all__'

class CreateTaskAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskAssignment
        fields = '__all__'
