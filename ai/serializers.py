# serializers.py
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers
from taggit.serializers import TagListSerializerField

from common.models import Document
from honeycomb.models import Bee, Hive


User = get_user_model()


class HiveAssistantRequestSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=1000)
    additional_instructions = serializers.CharField(max_length=1000, required=False, allow_blank=True)








class UserSerializer(serializers.ModelSerializer):


    class Meta:
        model = User
        fields = "__all__"
        ref_name = 'AppUser'


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
        fields = ['bee', 'feedback_aggregates']