from rest_framework import serializers


class StandardResponseSerializer(serializers.Serializer):
    error = serializers.BooleanField(required=False)
    success = serializers.BooleanField(required=False)
    message = serializers.CharField(required=False)
    data = serializers.JSONField(required=False)


class ErrorResponseSerializer(serializers.Serializer):
    error = serializers.BooleanField(default=True)
    message = serializers.CharField()


class PaginationResponseSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    next = serializers.CharField(allow_null=True, required=False)
    previous = serializers.CharField(allow_null=True, required=False)
    results = serializers.ListField(child=serializers.JSONField())
