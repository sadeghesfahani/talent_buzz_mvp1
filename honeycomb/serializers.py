from rest_framework import serializers
from taggit.serializers import TagListSerializerField

from common.serializers import DocumentSerializer
from user.serializers import UserSerializer
from .models import Hive, Bee, Membership, Nectar, HiveRequest, Contract, Report


class BeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bee
        fields = '__all__'


class HiveSerializer(serializers.ModelSerializer):
    tags = TagListSerializerField()
    admins = UserSerializer(many=True, read_only=True)
    hive_bees = BeeSerializer(many=True, read_only=True)

    class Meta:
        model = Hive
        fields = '__all__'


class NectarSerializer(serializers.ModelSerializer):
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


class HiveRequestSerializer(serializers.ModelSerializer):
    bee = BeeWithDetailSerializer(read_only=True)

    class Meta:
        model = HiveRequest
        fields = '__all__'


class ContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contract
        fields = '__all__'


class MembershipAcceptSerializer(serializers.Serializer):
    hive_request_id = serializers.IntegerField(required=True)


class MembershipSubmitSerializer(serializers.Serializer):
    hive = serializers.IntegerField(required=True)


class ReportSerializer(serializers.ModelSerializer):
    hive = HiveSerializer(read_only=True)
    nectar = NectarSerializer(read_only=True)
    bee = BeeSerializer(read_only=True)

    class Meta:
        model = Report
        fields = '__all__'


class MembershipSerializer(serializers.ModelSerializer):
    hive = HiveSerializer(read_only=True)
    bee = BeeWithDetailSerializer(read_only=True)

    class Meta:
        model = Membership
        fields = '__all__'
