# Rest Framework
from rest_framework import serializers

class VolumenNegocioSerializer(serializers.Serializer):
    month = serializers.CharField()
    volumen_originado = serializers.FloatField()
    volumen_acumulado = serializers.FloatField()


class DashboardSerializer(serializers.Serializer):
    totalOperaciones = serializers.IntegerField()
    cantidad_facturas = serializers.IntegerField()
    tasa_descuento_promedio = serializers.FloatField()
    saldo_disponible = serializers.FloatField()
    tasa_inversionista_promedio = serializers.FloatField()
    plazo_originacion_promedio = serializers.FloatField()
    volumen_negocio = VolumenNegocioSerializer(many=True, required=False)

    class Meta:
        fields = [
            'totalOperaciones',
            'cantidad_facturas',
            'tasa_descuento_promedio',
            'saldo_disponible',
            'tasa_inversionista_promedio',
            'plazo_originacion_promedio',
            'volumen_negocio'
        ]
