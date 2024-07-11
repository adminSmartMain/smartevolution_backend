
# Rest Framework
from rest_framework import serializers
# Models
from apps.misc.models import Department
# Utils
from apps.base.utils.index import gen_uuid
from django.utils import timezone
# Exceptions
from apps.base.exceptions import HttpException


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        id = serializers.CharField(style={'input_type': 'text'}, write_only=True)
        model  = Department
        fields = "__all__"



    def create(self, validated_data):
        if ('description' in validated_data) == False:
            raise HttpException(400, 'The description is required.')

        if len(validated_data['description']) < 3:
            raise HttpException(400, 'The description must have at least 3 characters.')
        
        validated_data['id'] = gen_uuid()
        validated_data['created_at'] = timezone.now()
        validated_data['user_created_at'] = self.context['request'].user
        return Department.objects.create(**validated_data)

    def update(self, instance, validated_data):
        if ('description' in validated_data):
            if len(validated_data['description']) < 3:
                raise HttpException(400, 'The description must have at least 3 characters.')

        instance.updated_at = timezone.now()

        return super().update(instance, validated_data)