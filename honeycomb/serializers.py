from rest_framework import serializers
from taggit.serializers import TagListSerializerField

from common.models import Document
from common.serializers import DocumentSerializer
from user.serializers import UserSerializer
from .models import Hive, Bee, Membership, Nectar, HiveRequest, Contract, Report


class BeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bee
        fields = '__all__'




class BeeWithDetailSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Bee
        fields = '__all__'
class HiveWiThDetailsSerializer(serializers.ModelSerializer):
    hive_bees = BeeWithDetailSerializer(many=True)

    class Meta:
        model = Hive
        fields = '__all__'

class NectarSerializer(serializers.ModelSerializer):
    nectar_hive = HiveWiThDetailsSerializer(read_only=True)
    tags = TagListSerializerField()
    documents = serializers.ListField(
        child=serializers.FileField(max_length=100000, allow_empty_file=False, use_url=False),
        write_only=True,
        required=False
    )
    uploaded_documents = DocumentSerializer(many=True, read_only=True, source='documents')

    class Meta:
        model = Nectar
        fields = '__all__'








class HiveRequestSerializer(serializers.ModelSerializer):
    bee = BeeWithDetailSerializer(read_only=True)

    class Meta:
        model = HiveRequest
        fields = '__all__'


class ContractSerializer(serializers.ModelSerializer):
    bees_with_detail = serializers.SerializerMethodField()

    class Meta:
        model = Contract
        fields = '__all__'

    def get_bees_with_detail(self, obj):
        if obj.bee is not None:
            return BeeWithDetailSerializer(obj.bee).data
        else:
            return None  # Or provide some default data


class MembershipAcceptSerializer(serializers.Serializer):
    hive_request_id = serializers.IntegerField(required=True)


class MembershipSubmitSerializer(serializers.Serializer):
    hive = serializers.IntegerField(required=True)


class HiveSerializer(serializers.ModelSerializer):
    tags = TagListSerializerField()
    admins = UserSerializer(many=True, read_only=True)
    hive_bees = BeeSerializer(many=True, read_only=True)
    nectars = NectarSerializer(many=True, read_only=True)

    class Meta:
        model = Hive
        fields = '__all__'

    def create(self, validated_data):
        tags = validated_data.pop('tags', [])
        print(tags)
        hive = super().create(validated_data)
        hive.tags.set(tags)  # Assuming tags are a ManyToMany field
        return hive

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', [])
        instance = super().update(instance, validated_data)
        instance.tags.set(tags)  # Assuming tags are a ManyToMany field
        return instance


class CreateHiveRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = HiveRequest
        fields = '__all__'


# class ContractSerializer(serializers.ModelSerializer):
#     bees_with_detail = serializers.SerializerMethodField()
#     nectar = NectarSerializer(read_only=True)
#
#     class Meta:
#         model = Contract
#         fields = "__all__"

class CreateContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contract
        fields = '__all__'



class ReportSerializer(serializers.ModelSerializer):
    hive = HiveSerializer(read_only=True)
    nectar = NectarSerializer(read_only=True)
    bee = BeeSerializer(read_only=True)

    class Meta:
        model = Report
        fields = '__all__'


class CreateReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = '__all__'


class CreateNectarSerializer(serializers.ModelSerializer):
    tags = TagListSerializerField()
    documents = serializers.ListField(
        child=serializers.FileField(max_length=100000, allow_empty_file=False, use_url=False),
        write_only=True,
        required=False
    )
    uploaded_documents = DocumentSerializer(many=True, read_only=True, source='documents')

    class Meta:
        model = Nectar
        fields = '__all__'

    def create(self, validated_data):
        document_files = validated_data.pop('documents', [])
        nectar = Nectar.objects.create(**validated_data)

        # Handling document saving
        for doc_file in document_files:
            document = Document.objects.create(file=doc_file)
            nectar.documents.add(document)

        return nectar


class MembershipSerializer(serializers.ModelSerializer):
    hive = HiveSerializer(read_only=True)
    bee = BeeWithDetailSerializer(read_only=True)
    assigned_tasks = serializers.SerializerMethodField()
    task_assignments = serializers.SerializerMethodField()

    class Meta:
        model = Membership
        fields = '__all__'

    def get_assigned_tasks(self, obj):
        from task.models import Task
        from task.serializers import TaskSerializer
        tasks = Task.objects.filter(assigned_bees=obj.bee)
        return TaskSerializer(tasks, many=True).data

    def get_task_assignments(self, obj):
        from task.models import TaskAssignment
        from task.serializers import TaskAssignmentSerializer
        task_assignments = TaskAssignment.objects.filter(bee=obj.bee, is_active=True)
        return TaskAssignmentSerializer(task_assignments, many=True).data
