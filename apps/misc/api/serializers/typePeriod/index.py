# Rest Framework
from rest_framework import serializers
# Models
from apps.misc.models import TypePeriod, PeriodRange
# Utils
from django.utils import timezone
from apps.base.utils.index import gen_uuid
# Exceptions
from apps.base.exceptions import HttpException

class TypePeriodSerializer(serializers.ModelSerializer):
    class Meta:
        model = TypePeriod
        fields = "__all__"


    def create(self, validated_data):
        if ('description' in validated_data) == False:
            raise HttpException(400, 'The description is required.')

        if len(validated_data['description']) < 3:
            raise HttpException(400, 'The description must have at least 3 characters.')

        validated_data['id']              = gen_uuid()
        validated_data['created_at']      = timezone.now()
        validated_data['user_created_at'] = self.context['request'].user
        return TypePeriod.objects.create(**validated_data)

    def update(self, instance, validated_data):
        if ('description' in validated_data):
            if len(validated_data['description']) < 3:
                raise HttpException(400, 'The description must have at least 3 characters.')

        instance.updated_at = timezone.now()
        instance.user_updated_at = self.context['request'].user

        return super().update(instance, validated_data)


class TypePeriodReadOnlySerializer(serializers.ModelSerializer):
    periodRange = serializers.SerializerMethodField(method_name='get_period_range')
    subPeriods = serializers.SerializerMethodField(method_name='get_sub_periods')
    class Meta:
        model = TypePeriod
        fields = "__all__"

    def get_period_range(self, obj):
        if obj.id == '0835dcb5-d6f2-43d7-b7ca-8864119ea05f':
            return False
        elif obj.id == 'e635f0f1-b29c-45e5-b351-04725a489be3':
            return False
        elif obj.id == 'e7b663d7-5cc3-4a9f-b288-95ce38c1ccfd':
            return False
        else:
            return True

    def get_sub_periods(self, obj):
        if obj.id == 'e635f0f1-b29c-45e5-b351-04725a489be3':
            subPeriods = []
            ranges = PeriodRange.objects.filter(description__icontains='semestre')
            for x in ranges:
                subPeriods.append({
                    'id': x.id,
                    'description': x.description,
                })
            return subPeriods
        elif obj.id == 'e7b663d7-5cc3-4a9f-b288-95ce38c1ccfd':
            subPeriods = []
            ranges = PeriodRange.objects.filter(description__icontains='trimestre')
            for x in ranges:
                subPeriods.append({
                    'id': x.id,
                    'description': x.description,
                })
            return subPeriods
        else:
            return None


