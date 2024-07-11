# Rest Framework
from rest_framework import serializers
# Models
from apps.misc.models import City
# Serializers
from apps.misc.api.serializers.department.index import DepartmentSerializer
# Utils
from django.utils import timezone
from apps.base.utils.index import gen_uuid
# Exceptions
from apps.base.exceptions import HttpException


class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model  = City
        fields = "__all__"

    def create(self, validated_data):

        if ('department' in validated_data) == False:
            raise HttpException(400, 'The department is required.')

        if ('description' in validated_data) == False:
            raise HttpException(400, 'The description is required.')

        if len(validated_data['description']) < 3:
            raise HttpException(400, 'The description must have at least 3 characters.')

        validated_data['id'] = gen_uuid()
        validated_data['created_at'] = timezone.now()
        validated_data['user_created_at'] = self.context['request'].user
        return City.objects.create(**validated_data)

    def update(self, instance, validated_data):
        if ('description' in validated_data):
            if len(validated_data['description']) < 3:
                raise HttpException(400, 'The description must have at least 3 characters.')

        instance.updated_at = timezone.now()
        instance.user_updated_at = self.context['request'].user

        return super().update(instance, validated_data)
    


class CityReadOnlySerializer(serializers.ModelSerializer):
    department = DepartmentSerializer(read_only=True)
    class Meta:
        model  = City
        fields = "__all__"