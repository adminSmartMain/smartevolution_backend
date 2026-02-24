# En apps/operation/api/serializers/dashboard/index.py
from rest_framework import serializers

class VolumenNegocioSerializer(serializers.Serializer):
    month = serializers.CharField()
    volumen_originado = serializers.FloatField()
    volumen_acumulado = serializers.FloatField()

class TendenciaSerializer(serializers.Serializer):
    percentage = serializers.FloatField()
    description = serializers.CharField()
    trend = serializers.CharField()
    current_value = serializers.FloatField()
    previous_value = serializers.FloatField()

class DashboardSerializer(serializers.Serializer):
    totalOperaciones = serializers.IntegerField()
    cantidad_facturas = serializers.IntegerField()
    tasa_descuento_promedio = serializers.FloatField()
    saldo_disponible = serializers.FloatField()
    tasa_inversionista_promedio = serializers.FloatField()
    plazo_originacion_promedio = serializers.FloatField()
    plazo_recaudo_promedio = serializers.FloatField()
    valor_total_portafolio = serializers.FloatField()
    volumen_negocio = VolumenNegocioSerializer(many=True, required=False)
    tendencias = serializers.DictField(child=TendenciaSerializer(), required=False)
    ultima_actualizacion = serializers.CharField(required=False)  # NUEVO CAMPO

    class Meta:
        fields = [
            'totalOperaciones',
            'cantidad_facturas',
            'tasa_descuento_promedio',
            'saldo_disponible',
            'tasa_inversionista_promedio',
            'plazo_originacion_promedio',
            'plazo_recaudo_promedio',
            'valor_total_portafolio',
            'volumen_negocio',
            'tendencias',
            'ultima_actualizacion'  # NUEVO CAMPO
        ]