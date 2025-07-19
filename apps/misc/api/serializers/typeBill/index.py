from rest_framework import serializers
from apps.misc.models import TypeBill

class TypeBillSerializer(serializers.ModelSerializer):
    class Meta:
        model = TypeBill
        fields = '__all__'
       
    
