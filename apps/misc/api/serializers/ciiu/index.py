# Rest Framework
from rest_framework import serializers
# Models
from apps.misc.models import CIIU
# Serializers
from apps.misc.api.serializers.activity.index import ActivityReadOnlySerializer
from apps.misc.api.serializers.section.index import SectionReadOnlySerializer
# Utils
from django.utils import timezone
from apps.base.utils.index import gen_uuid
# Exceptions
from apps.base.exceptions import HttpException


class CIIUSerializer(serializers.ModelSerializer):
    class Meta:
        model  = CIIU
        fields = "__all__"
        
    def create(self, validated_data):

        if ('code' in validated_data) == False:
            raise HttpException(400, 'The code is required.')

        if ('section' in validated_data) == False:
            raise HttpException(400, 'The section is required.')

        if ('activity' in validated_data) == False:
            raise HttpException(400, 'The activity is required.')

        validated_data['id'] = gen_uuid()
        validated_data['created_at'] = timezone.now()
        validated_data['user_created_at'] = self.context['request'].user
        return CIIU.objects.create(**validated_data)

    def update(self, instance, validated_data):
        
        instance.updated_at = timezone.now()
        instance.user_updated_at = self.context['request'].user

        return super().update(instance, validated_data)



class CIIUReadOnlySerializer(serializers.ModelSerializer):
    activity = ActivityReadOnlySerializer(read_only=True)
    class Meta:
        model  = CIIU
        fields = "__all__"
    