from rest_framework import serializers

from common.models import Document
from common.serializers import DocumentSerializer
from honeycomb.serializers import ContractSerializer, BeeWithDetailSerializer
from task.models import Task, TaskAssignment


class TaskSerializer(serializers.ModelSerializer):
    contract = ContractSerializer(read_only=True)
    uploaded_documents = DocumentSerializer(many=True, read_only=True, source='documents')

    class Meta:
        model = Task
        fields = '__all__'

class CreateTaskSerializer(serializers.ModelSerializer):
    documents = serializers.ListField(
        child=serializers.FileField(max_length=100000, allow_empty_file=False, use_url=False),
        write_only=True,
        required=False
    )

    class Meta:
        model = Task
        fields = '__all__'

    def create(self, validated_data):
        document_files = validated_data.pop('documents', [])
        task = Task.objects.create(**{k: v for k, v in validated_data.items() if k not in ['documents', 'admins', 'assigned_bees']})

        # Handling document saving
        for doc_file in document_files:
            document = Document.objects.create(document=doc_file, user=self.context['request'].user)
            task.documents.add(document)

        return task


class TaskAssignmentSerializer(serializers.ModelSerializer):
    bee = BeeWithDetailSerializer(read_only=True)
    class Meta:
        model = TaskAssignment
        fields = '__all__'

class CreateTaskAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskAssignment
        fields = '__all__'
