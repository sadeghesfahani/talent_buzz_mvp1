# serializers.py
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers
from taggit.serializers import TagListSerializerField

from common.models import Document
from honeycomb.models import Bee, Hive
from user.models import PersonalDetails, CompanyDetails, FreelancerDetails

User = get_user_model()


class HiveAssistantRequestSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=1000)
    additional_instructions = serializers.CharField(max_length=1000, required=False, allow_blank=True)


class PersonalDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PersonalDetails  # Assuming this is the model for personal details
        fields = ['first_name', 'last_name', 'measures']


class CompanyDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyDetails  # Assuming this is the model for company details
        fields = ['company_name', 'company_description', 'company_specialities', 'company_social_media']


class FreelancerDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = FreelancerDetails  # Assuming this is the model for freelancer details
        fields = '__all__'  # Assuming all fields are needed for freelancer details


class UserSerializer(serializers.ModelSerializer):
    personal_details = PersonalDetailsSerializer()
    company_details = CompanyDetailsSerializer()
    freelancer_details = FreelancerDetailsSerializer()

    class Meta:
        model = User
        fields = ['personal_details', 'company_details', 'freelancer_details']


class BeeSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Bee
        fields = "__all__"


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        exclude = ['created_at', 'document']


class HiveSerializer(serializers.ModelSerializer):
    tags = TagListSerializerField()
    admins = UserSerializer(many=True, read_only=True)
    hive_bees = BeeSerializer(many=True, read_only=True)
    documents = DocumentSerializer(many=True, read_only=True)

    class Meta:
        model = Hive
        fields = ['name', 'description', 'admins', 'hive_bees', 'hive_requirements', 'is_public', 'documents', 'tags']


class UserWithDetailsSerializer(serializers.ModelSerializer):
    personal_details = PersonalDetailsSerializer(required=False)
    company_details = CompanyDetailsSerializer(required=False)
    freelancer_details = FreelancerDetailsSerializer(required=False)
    feedback_aggregates = serializers.SerializerMethodField()
    bee = serializers.SerializerMethodField()

    def get_bee(self, obj):
        from honeycomb.serializers import BeeSerializer
        try:
            bee = obj.bee
        except ObjectDoesNotExist:
            return None
        return BeeSerializer(bee).data

    @staticmethod
    def get_feedback_aggregates(obj):
        return obj.get_feedback_aggregates()

    class Meta:
        model = User
        fields = ['personal_details', 'company_details', 'freelancer_details', 'bee', 'feedback_aggregates']