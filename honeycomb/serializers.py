from rest_framework import serializers

from .models import Hive, Bee, Membership, Nectar, HiveRequest, Contract


class HiveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hive
        fields = '__all__'


class BeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bee
        fields = '__all__'


class MembershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Membership
        fields = '__all__'


class NectarSerializer(serializers.ModelSerializer):
    class Meta:
        model = Nectar
        fields = '__all__'


class HiveRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = HiveRequest
        fields = '__all__'


class ContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contract
        fields = '__all__'
