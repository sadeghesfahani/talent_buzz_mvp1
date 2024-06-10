from rest_framework import serializers
from honeycomb.serializers import ContractSerializer
from task.models import Task, TaskAssignment


class TaskSerializer(serializers.ModelSerializer):
    contract = ContractSerializer()

    class Meta:
        model = Task
        fields = '__all__'


class TaskAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskAssignment
        fields = '__all__'
