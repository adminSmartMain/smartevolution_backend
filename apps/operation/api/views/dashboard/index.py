# REST Framework imports
from rest_framework.decorators import APIView
from django.db.models import Q, Count, Avg, Sum
from rest_framework import serializers
# Models
from apps.client.models import Client, RiskProfile, Account, Broker
from apps.operation.models import PreOperation, Receipt, BuyOrder
from apps.bill.models import Bill
from apps.misc.models import TypeBill
# Serializers
from apps.operation.api.serializers.index import (
    PreOperationSerializer, PreOperationReadOnlySerializer, 
    ReceiptSerializer, PreOperationSignatureSerializer, PreOperationByParamsSerializer
)
# Utils
from apps.base.utils.index import response, gen_uuid, BaseAV
from apps.report.utils.index import generateSellOffer, calcOperationDetail
import pandas as pd
import json
from time import strftime, localtime
from functools import reduce
# Decorators
from apps.base.decorators.index import checkRole
#utils
from apps.base.utils.logBalanceAccount import log_balance_change
import logging

from django.db import transaction
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
import uuid
from apps.base.utils.index import gen_uuid, PDFBase64File, uploadFileBase64
from apps.operation.api.serializers.dashboard.index import DashboardSerializer
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from django.db.models.functions import TruncMonth

# =======================
# Configurar el logger
# =======================
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


def is_uuid(val):
    try:
        uuid.UUID(str(val))
        return True
    except ValueError:
        return False


class DashboardAV(BaseAV):
    def get(self, request):
        try:
            # ==========================
            # 📋 Obtener filtros
            # ==========================
            filters = self._get_filters(request)
            
            # Aplicar filtros base
            queryset = PreOperation.objects.filter(**filters)
            
            # ==========================
            # 📊 Calcular métricas globales
            # ==========================
            total_operaciones = queryset.count()
            cantidad_facturas = queryset.values('bill').distinct().count()
            
            metrics = queryset.aggregate(
                avg_discount=Avg('discountTax'),
                avg_investor_tax=Avg('investorTax'),
                avg_operation_days=Avg('operationDays'),
                total_amount=Sum('amount'),
                total_payed=Sum('payedAmount'),
                monto_pendiente=Sum('opPendingAmount')
            )
    
            tasa_descuento_promedio = metrics['avg_discount'] or 0
            tasa_inversionista_promedio = metrics['avg_investor_tax'] or 0
            plazo_originacion_promedio = metrics['avg_operation_days'] or 0
            saldo_disponible = (metrics['total_amount'] or 0) - (metrics['total_payed'] or 0)

            # ==========================
            # 📈 Volumen originado/acumulado
            # ==========================
            monthly_data = (
                queryset
                .annotate(month=TruncMonth('opDate'))
                .values('month')
                .annotate(volumen_originado=Sum('payedAmount'))
                .order_by('month')
            )

            acumulado = 0
            volumen_chart = []
            for item in monthly_data:
                volumen_mes = float(item['volumen_originado'] or 0)
                acumulado += volumen_mes
                volumen_chart.append({
                    'month': item['month'].strftime('%B'),
                    'volumen_originado': volumen_mes,
                    'volumen_acumulado': round(acumulado, 2)
                })

            # ==========================
            # 📦 Estructura de salida
            # ==========================
            data = {
                'totalOperaciones': total_operaciones,
                'cantidad_facturas': cantidad_facturas,
                'tasa_descuento_promedio': round(tasa_descuento_promedio, 2),
                'tasa_inversionista_promedio': round(tasa_inversionista_promedio, 2),
                'plazo_originacion_promedio': round(plazo_originacion_promedio, 2),
                'saldo_disponible': round(saldo_disponible, 2),
                'volumen_negocio': volumen_chart  # 👈 agregado aquí
            }
            
            serializer = DashboardSerializer(data)
            return Response({
                'success': True,
                'data': serializer.data,
                'filters_applied': self._get_applied_filters_info(request)
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error en dashboard: {str(e)}")
            return Response({
                'success': False,
                'error': 'Error al obtener datos del dashboard'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ===================================================
    # 🔍 Construcción de filtros, incluyendo "periodo"
    # ===================================================
    def _get_filters(self, request):
        filters = {}
        
        # Filtro por periodo genérico
        periodo = request.GET.get('periodo')
        hoy = date.today()

        if periodo:
            if periodo == "este_anio":
                inicio = date(hoy.year, 1, 1)
                fin = date(hoy.year, 12, 31)
                filters['opDate__range'] = [inicio, fin]

            elif periodo == "este_mes":
                inicio = date(hoy.year, hoy.month, 1)
                fin = (inicio + relativedelta(months=1)) - timedelta(days=1)
                filters['opDate__range'] = [inicio, fin]

            elif periodo == "esta_semana":
                inicio = hoy - timedelta(days=hoy.weekday())
                fin = inicio + timedelta(days=6)
                filters['opDate__range'] = [inicio, fin]

            elif periodo.isdigit() and len(periodo) == 4:
                anio = int(periodo)
                inicio = date(anio, 1, 1)
                fin = date(anio, 12, 31)
                filters['opDate__range'] = [inicio, fin]

            elif periodo == "ultimo_trimestre":
                mes_actual = hoy.month
                trimestre_inicio = mes_actual - ((mes_actual - 1) % 3)
                inicio = date(hoy.year, trimestre_inicio, 1)
                fin = (inicio + relativedelta(months=3)) - timedelta(days=1)
                filters['opDate__range'] = [inicio, fin]

        # Filtro manual por fechas exactas
        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin = request.GET.get('fecha_fin')
        if fecha_inicio and fecha_fin:
            try:
                filters['opDate__range'] = [fecha_inicio, fecha_fin]
            except ValueError:
                pass

        # ====================================
        # 🔎 Resto de filtros tradicionales
        # ====================================
        ids = {
            'emitter_id': 'emitter_id',
            'payer_id': 'payer_id',
            'investor_id': 'investor_id',
            'client_account_id': 'clientAccount_id',
            'op_type_id': 'opType_id',
            'emitter_broker_id': 'emitterBroker_id',
            'investor_broker_id': 'investorBroker_id'
        }

        for param, field in ids.items():
            val = request.GET.get(param)
            if val:
                if is_uuid(val):
                    filters[field] = val
                else:
                    try:
                        filters[field] = int(val)
                    except ValueError:
                        pass
        
        # Estado
        status_filter = request.GET.get('status')
        if status_filter:
            try:
                filters['status'] = int(status_filter)
            except ValueError:
                pass
        
        # Recompra
        is_rebuy = request.GET.get('is_rebuy')
        if is_rebuy in ['true', 'false']:
            filters['isRebuy'] = is_rebuy.lower() == 'true'
        
        return filters

    def _get_applied_filters_info(self, request):
        """
        Retorna información sobre los filtros aplicados
        """
        applied_filters = {}
        filter_mapping = {
            'fecha_inicio': 'Fecha inicio',
            'fecha_fin': 'Fecha fin',
            'periodo': 'Periodo',
            'emitter_id': 'Emisor',
            'payer_id': 'Pagador',
            'investor_id': 'Inversionista',
            'client_account_id': 'Cuenta cliente',
            'status': 'Estado',
            'op_type_id': 'Tipo operación',
            'emitter_broker_id': 'Broker emisor',
            'investor_broker_id': 'Broker inversionista',
            'is_rebuy': 'Es recompra'
        }
        
        for param, description in filter_mapping.items():
            value = request.GET.get(param)
            if value:
                applied_filters[description] = value
        
        return applied_filters
