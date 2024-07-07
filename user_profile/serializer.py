from rest_framework import serializers
from user.models import User
from user.serializers import UserSerializer
from honeycomb.models import Hive, Membership, Contract
from task.models import TaskAssignment
from feedback.models import Feedback

class HiveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hive
        fields = ['id', 'name', 'description', 'hive_type']

class MembershipSerializer(serializers.ModelSerializer):
    hive = HiveSerializer()

    class Meta:
        model = Membership
        fields = ['hive', 'is_accepted', 'joined_at']

class ContractSerializer(serializers.ModelSerializer):
    nectar = serializers.StringRelatedField()

    class Meta:
        model = Contract
        fields = ['nectar', 'accepted_rate', 'is_accepted', 'accepted_at', 'completed_at']

class TaskAssignmentSerializer(serializers.ModelSerializer):
    task = serializers.StringRelatedField()

    class Meta:
        model = TaskAssignment
        fields = ['task', 'assigned_at', 'is_accepted', 'accepted_at']

class FeedbackSerializer(serializers.ModelSerializer):
    contract = ContractSerializer()
    author = UserSerializer()

    class Meta:
        model = Feedback
        fields = ['contract', 'communication', 'quality_of_work', 'punctuality', 'overall_satisfaction', 'experience', 'created_at', 'author']

class UserProfileSerializer(serializers.ModelSerializer):
    created_hives = serializers.SerializerMethodField()
    member_hives = serializers.SerializerMethodField()
    contract_count = serializers.SerializerMethodField()
    task_assignment_count = serializers.SerializerMethodField()
    feedbacks = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'created_hives', 'member_hives',
            'contract_count', 'task_assignment_count', 'feedbacks', 'avatar', 'freelancer_details'
        ]

    def get_created_hives(self, obj):
        hives = Hive.objects.filter(admins=obj)
        return HiveSerializer(hives, many=True).data

    def get_member_hives(self, obj):
        memberships = Membership.objects.filter(bee__user=obj, is_accepted=True)
        return MembershipSerializer(memberships, many=True).data

    def get_contract_count(self, obj):
        return Contract.objects.filter(bee__user=obj, is_accepted=True).count()

    def get_task_assignment_count(self, obj):
        return TaskAssignment.objects.filter(bee__user=obj, is_accepted=True).count()

    def get_feedbacks(self, obj):
        feedbacks = Feedback.objects.filter(recipient=obj)
        return FeedbackSerializer(feedbacks, many=True).data
