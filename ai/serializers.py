# serializers.py
from rest_framework import serializers

class HiveAssistantRequestSerializer(serializers.Serializer):
    hive_id = serializers.CharField(max_length=100)
    message = serializers.CharField(max_length=1000)
    thread_id = serializers.CharField(max_length=100, required=False, allow_blank=True)
