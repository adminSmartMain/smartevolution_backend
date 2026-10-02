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


class ClienteRolSerializer(serializers.Serializer):
    role = serializers.CharField()
    count = serializers.IntegerField()
    percentage_of_clients = serializers.FloatField()


class TopEmitterSerializer(serializers.Serializer):
    client_id = serializers.CharField(allow_null=True, required=False)
    document_number = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    name = serializers.CharField()
    invoice_count = serializers.IntegerField()
    invoice_value = serializers.FloatField()


class TopInvestorSerializer(serializers.Serializer):
    client_id = serializers.CharField()
    document_number = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    name = serializers.CharField()
    operations = serializers.IntegerField()
    invested_value = serializers.FloatField()


class ClientesDashboardSerializer(serializers.Serializer):
    total = serializers.IntegerField()
    total_role_assignments = serializers.IntegerField()
    por_rol = ClienteRolSerializer(many=True)
    top_emitters = TopEmitterSerializer(many=True)
    top_investors = TopInvestorSerializer(many=True)


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
    clientes = ClientesDashboardSerializer(required=False)
    tendencias = serializers.DictField(child=TendenciaSerializer(), required=False)
    ultima_actualizacion = serializers.CharField(required=False)
