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
from datetime import date, timedelta, datetime
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
            periodo = request.GET.get('periodo', 'este_anio')
            
            # ==========================
            # 📊 Calcular métricas actuales
            # ==========================
            current_data = self._calculate_current_metrics(filters, periodo)
            
            # ==========================
            # 📈 Calcular tendencias
            # ==========================
            trends = self._calculate_trends(current_data, periodo, filters)
            
            # ==========================
            # 🕐 Obtener fecha de última actualización
            # ==========================
            ultima_actualizacion = self._get_ultima_actualizacion(filters)
            
            # ==========================
            # 📦 Estructura de salida
            # ==========================
            data = {
                **current_data, 
                'tendencias': trends,
                'ultima_actualizacion': ultima_actualizacion
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

    def _get_ultima_actualizacion(self, filters):
        """
        Obtiene la fecha de la última operación creada para mostrar como "Actualizado:"
        """
        try:
            # Buscar la última operación por created_at
            ultima_operacion = PreOperation.objects.filter(**filters).order_by('-created_at').first()
            
            if ultima_operacion and ultima_operacion.created_at:
                # Formatear la fecha en español
                fecha_formateada = ultima_operacion.created_at.strftime('%d/%m/%Y %H:%M:%S')
                logger.info(f"📅 Última actualización encontrada: {fecha_formateada}")
                return fecha_formateada
            else:
                # Si no hay operaciones, usar la fecha actual
                fecha_actual = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
                logger.info(f"📅 No hay operaciones, usando fecha actual: {fecha_actual}")
                return fecha_actual
                
        except Exception as e:
            logger.error(f"Error obteniendo última actualización: {str(e)}")
            # Fallback a fecha actual
            return datetime.now().strftime('%d/%m/%Y %H:%M:%S')

    def _calculate_current_metrics(self, filters, periodo):
        """
        Calcula todas las métricas para el período actual
        """
        queryset = PreOperation.objects.filter(**filters)
        
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
        # 🔄 NUEVAS MÉTRICAS AGREGADAS
        # ==========================
        plazo_recaudo_promedio = self._get_plazo_recaudo_promedio(filters)
        valor_total_portafolio = self._get_valor_total_portafolio(saldo_disponible)
        
        # ==========================
        # 📈 Volumen de negocio
        # ==========================
        volumen_chart = self._get_volumen_negocio(queryset, periodo)

        return {
            'totalOperaciones': total_operaciones,
            'cantidad_facturas': cantidad_facturas,
            'tasa_descuento_promedio': round(tasa_descuento_promedio, 2),
            'tasa_inversionista_promedio': round(tasa_inversionista_promedio, 2),
            'plazo_originacion_promedio': round(plazo_originacion_promedio, 2),
            'plazo_recaudo_promedio': round(plazo_recaudo_promedio, 2),
            'saldo_disponible': round(saldo_disponible, 2),
            'valor_total_portafolio': round(valor_total_portafolio, 2),
            'volumen_negocio': volumen_chart
        }

    def _get_comparison_period(self, periodo, current_filters):
        """
        Determina el período de comparación basado en created_at
        """
        hoy = datetime.now().date()
        
        if periodo == "este_mes":
            # Mes actual vs Mes anterior
            inicio_actual = date(hoy.year, hoy.month, 1)
            fin_actual = hoy
            
            inicio_anterior = (inicio_actual - relativedelta(months=1))
            fin_anterior = (fin_actual - relativedelta(months=1))
            
            return {
                'current': ['created_at__range', [inicio_actual, fin_actual]],
                'previous': ['created_at__range', [inicio_anterior, fin_anterior]],
                'description': 'vs mes anterior'
            }
        
        elif periodo == "esta_semana":
            # Semana actual vs Semana anterior
            inicio_actual = hoy - timedelta(days=hoy.weekday())
            fin_actual = hoy
            
            inicio_anterior = inicio_actual - timedelta(days=7)
            fin_anterior = fin_actual - timedelta(days=7)
            
            return {
                'current': ['created_at__range', [inicio_actual, fin_actual]],
                'previous': ['created_at__range', [inicio_anterior, fin_anterior]],
                'description': 'vs semana anterior'
            }
        
        elif periodo == "este_anio":
            # Año actual vs Año anterior
            inicio_actual = date(hoy.year, 1, 1)
            fin_actual = hoy
            
            inicio_anterior = date(hoy.year - 1, 1, 1)
            fin_anterior = date(hoy.year - 1, 12, 31)
            
            return {
                'current': ['created_at__range', [inicio_actual, fin_actual]],
                'previous': ['created_at__range', [inicio_anterior, fin_anterior]],
                'description': 'vs año anterior'
            }
        
        elif periodo == "ultimo_trimestre":
            # Último trimestre vs Trimestre anterior
            trimestre_actual = (hoy.month - 1) // 3 + 1
            
            if trimestre_actual == 1:
                # Q1 actual vs Q4 anterior
                inicio_actual = date(hoy.year, 1, 1)
                fin_actual = date(hoy.year, 3, 31)
                inicio_anterior = date(hoy.year - 1, 10, 1)
                fin_anterior = date(hoy.year - 1, 12, 31)
            else:
                trimestre_anterior = trimestre_actual - 1
                mes_inicio_actual = (trimestre_anterior - 1) * 3 + 1
                mes_fin_actual = mes_inicio_actual + 2
                
                inicio_actual = date(hoy.year, mes_inicio_actual, 1)
                fin_actual = date(hoy.year, mes_fin_actual + 1, 1) - timedelta(days=1)
                
                inicio_anterior = inicio_actual - relativedelta(months=3)
                fin_anterior = fin_actual - relativedelta(months=3)
            
            return {
                'current': ['created_at__range', [inicio_actual, fin_actual]],
                'previous': ['created_at__range', [inicio_anterior, fin_anterior]],
                'description': 'vs trimestre anterior'
            }
        
        # Para años específicos (ej: "2024")
        elif periodo.isdigit() and len(periodo) == 4:
            anio_actual = int(periodo)
            anio_anterior = anio_actual - 1
            
            return {
                'current': ['created_at__range', [date(anio_actual, 1, 1), date(anio_actual, 12, 31)]],
                'previous': ['created_at__range', [date(anio_anterior, 1, 1), date(anio_anterior, 12, 31)]],
                'description': f'vs {anio_anterior}'
            }
        
        return None

    def _calculate_period_metrics(self, filters, period_filters):
        """
        Calcula las mismas métricas para un período específico usando created_at
        """
        try:
            # Crear nuevos filtros sin el rango de opDate original
            comparison_filters = {}
            
            # Copiar todos los filtros excepto opDate__range
            for key, value in filters.items():
                if key != 'opDate__range':
                    comparison_filters[key] = value
            
            # Aplicar filtro de created_at para el período
            filter_field, date_range = period_filters
            comparison_filters[filter_field] = date_range
            
            logger.info(f"🔍 Filtros de comparación aplicados: {comparison_filters}")
            
            queryset = PreOperation.objects.filter(**comparison_filters)
            
            # DEBUG: Verificar cuántos registros hay
            record_count = queryset.count()
            logger.info(f"📊 Registros encontrados en período de comparación: {record_count}")
            
            # Calcular métricas básicas
            total_operaciones = record_count
            cantidad_facturas = queryset.values('bill').distinct().count()
            
            metrics = queryset.aggregate(
                avg_discount=Avg('discountTax'),
                avg_investor_tax=Avg('investorTax'),
                total_amount=Sum('amount'),
                total_payed=Sum('payedAmount'),
            )
            
            saldo_disponible = (metrics['total_amount'] or 0) - (metrics['total_payed'] or 0)
            
            result = {
                'totalOperaciones': total_operaciones,
                'cantidad_facturas': cantidad_facturas,
                'tasa_descuento_promedio': metrics['avg_discount'] or 0,
                'tasa_inversionista_promedio': metrics['avg_investor_tax'] or 0,
                'saldo_disponible': saldo_disponible
            }
            
            logger.info(f"📈 Métricas de período calculadas: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error calculando métricas de período: {str(e)}")
            return {}

    def _calculate_trends(self, current_data, periodo, filters):
        """
        Calcula tendencias comparando período actual vs anterior usando created_at
        """
        try:
            logger.info(f"🔄 Calculando tendencias para período: {periodo}")
            
            # Obtener configuración de comparación
            comparison_config = self._get_comparison_period(periodo, filters)
            if not comparison_config:
                logger.info(f"❌ No hay comparación configurada para el período: {periodo}")
                return {}
            
            logger.info(f"📅 Comparación configurada: {comparison_config['description']}")
            
            # Calcular métricas para período anterior
            previous_data = self._calculate_period_metrics(
                filters, 
                comparison_config['previous']
            )
            
            # Si no hay datos del período anterior, no calcular tendencias
            if not previous_data:
                logger.info("❌ No se pudieron calcular métricas del período anterior")
                return {}
                
            # Verificar si hay datos suficientes
            if all(v == 0 for v in previous_data.values()):
                logger.info("❌ Todos los valores del período anterior son cero")
                return {}
            
            logger.info(f"📊 Datos período anterior: {previous_data}")
            logger.info(f"📊 Datos período actual: {current_data}")
            
            trends = {}
            trend_metrics = ['totalOperaciones', 'cantidad_facturas', 'saldo_disponible', 'tasa_descuento_promedio']
            
            for metric_key in trend_metrics:
                current_value = current_data.get(metric_key, 0)
                previous_value = previous_data.get(metric_key, 0)
                
                logger.info(f"📐 Comparando {metric_key}: Actual={current_value}, Anterior={previous_value}")
                
                # Solo calcular si hay datos suficientes en ambos períodos
                if previous_value > 0 and current_value > 0:
                    percentage_change = ((current_value - previous_value) / previous_value) * 100
                    
                    logger.info(f"📊 Cambio porcentual para {metric_key}: {percentage_change}%")
                    
                    # Solo mostrar cambios significativos (> 0.5%)
                    if abs(percentage_change) >= 0.5:
                        trends[metric_key] = {
                            'percentage': round(percentage_change, 1),
                            'description': comparison_config['description'],
                            'trend': 'up' if percentage_change > 0 else 'down',
                            'current_value': current_value,
                            'previous_value': previous_value
                        }
                        logger.info(f"✅ Tendencia significativa encontrada para {metric_key}: {percentage_change}%")
                    else:
                        logger.info(f"ℹ️  Cambio no significativo para {metric_key}: {percentage_change}%")
                else:
                    logger.info(f"❌ Datos insuficientes para calcular tendencia en {metric_key}")
            
            logger.info(f"🎯 Tendencias finales calculadas: {len(trends)} métricas")
            return trends
            
        except Exception as e:
            logger.error(f"❌ Error calculando tendencias: {str(e)}")
            import traceback
            logger.error(f"📋 Traceback: {traceback.format_exc()}")
            return {}

    def _get_plazo_recaudo_promedio(self, filters):
        """
        Calcula el promedio de realDays del modelo Receipts
        Aplica los mismos filtros de fecha que las preoperaciones
        """
        try:
            # Aplicar filtros de fecha a los receipts
            receipt_filters = {}
            
            # Copiar filtros de fecha de las preoperaciones
            if 'opDate__range' in filters:
                receipt_filters['operation__opDate__range'] = filters['opDate__range']
            
            # Calcular promedio de realDays
            plazo_promedio = Receipt.objects.filter(**receipt_filters).aggregate(
                avg_real_days=Avg('realDays')
            )['avg_real_days'] or 0
            
            return float(plazo_promedio)
            
        except Exception as e:
            logger.error(f"Error calculando plazo recaudo promedio: {str(e)}")
            return 0

    def _get_valor_total_portafolio(self, saldo_disponible):
        """
        Calcula el valor total del portafolio
        Por ahora: saldo_disponible + valor ficticio
        """
        try:
            # Valor ficticio para pruebas - puedes ajustar este cálculo
            valor_ficticio = 5000000  # 5 millones adicionales para pruebas
            
            valor_total = saldo_disponible + valor_ficticio
            return float(valor_total)
            
        except Exception as e:
            logger.error(f"Error calculando valor total del portafolio: {str(e)}")
            return saldo_disponible

    def _get_volumen_negocio(self, queryset, periodo):
        """
        Calcula el volumen de negocio según el período
        """
        from django.db.models.functions import TruncDay, TruncMonth
        from django.db.models import Sum
        
        hoy = date.today()
        volumen_data = []
        acumulado = 0

        if periodo in ['este_mes', 'esta_semana']:
            # Agrupar por DÍAS para períodos cortos
            daily_data = (
                queryset
                .annotate(day=TruncDay('opDate'))
                .values('day')
                .annotate(volumen_originado=Sum('payedAmount'))
                .order_by('day')
            )
            
            # Crear un diccionario para acceso rápido
            daily_dict = {item['day']: float(item['volumen_originado'] or 0) for item in daily_data}
            
            # Generar todos los días del período
            if periodo == 'este_mes':
                inicio = date(hoy.year, hoy.month, 1)
                fin = hoy
                current = inicio
                while current <= fin:
                    volumen_dia = daily_dict.get(current, 0)
                    acumulado += volumen_dia
                    volumen_data.append({
                        'month': current.strftime('%Y-%m-%d'),
                        'volumen_originado': volumen_dia,
                        'volumen_acumulado': round(acumulado, 2)
                    })
                    current += timedelta(days=1)
                    
            elif periodo == 'esta_semana':
                inicio = hoy - timedelta(days=hoy.weekday())
                fin = hoy
                current = inicio
                while current <= fin:
                    volumen_dia = daily_dict.get(current, 0)
                    acumulado += volumen_dia
                    dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
                    nombre_dia = dias_semana[current.weekday()]
                    volumen_data.append({
                        'month': nombre_dia,
                        'volumen_originado': volumen_dia,
                        'volumen_acumulado': round(acumulado, 2)
                    })
                    current += timedelta(days=1)
                
        else:
            # Agrupar por MESES para períodos largos
            monthly_data = (
                queryset
                .annotate(month=TruncMonth('opDate'))
                .values('month')
                .annotate(volumen_originado=Sum('payedAmount'))
                .order_by('month')
            )

            for item in monthly_data:
                volumen_mes = float(item['volumen_originado'] or 0)
                acumulado += volumen_mes
                volumen_data.append({
                    'month': item['month'].strftime('%B'),
                    'volumen_originado': volumen_mes,
                    'volumen_acumulado': round(acumulado, 2)
                })

        return volumen_data

    def _get_filters(self, request):
        filters = {}
        
        # Filtro por periodo genérico
        periodo = request.GET.get('periodo')
        hoy = date.today()

        if periodo:
            if periodo == "este_anio":
                inicio = date(hoy.year, 1, 1)
                fin = hoy
                filters['opDate__range'] = [inicio, fin]

            elif periodo == "este_mes":
                inicio = date(hoy.year, hoy.month, 1)
                fin = hoy
                filters['opDate__range'] = [inicio, fin]

            elif periodo == "esta_semana":
                inicio = hoy - timedelta(days=hoy.weekday())
                fin = hoy
                filters['opDate__range'] = [inicio, fin]

            elif periodo.isdigit() and len(periodo) == 4:
                anio = int(periodo)
                inicio = date(anio, 1, 1)
                fin = date(anio, 12, 31)
                filters['opDate__range'] = [inicio, fin]

            elif periodo == "ultimo_trimestre":
                trimestre_actual = (hoy.month - 1) // 3 + 1
                
                if trimestre_actual == 1:
                    inicio = date(hoy.year - 1, 10, 1)
                    fin = date(hoy.year - 1, 12, 31)
                else:
                    trimestre_anterior = trimestre_actual - 1
                    mes_inicio = (trimestre_anterior - 1) * 3 + 1
                    mes_fin = mes_inicio + 2
                    inicio = date(hoy.year, mes_inicio, 1)
                    if mes_fin == 12:
                        fin = date(hoy.year, 12, 31)
                    else:
                        fin = date(hoy.year, mes_fin + 1, 1) - timedelta(days=1)
                    
                filters['opDate__range'] = [inicio, fin]

        # Filtro manual por fechas exactas
        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin = request.GET.get('fecha_fin')
        if fecha_inicio and fecha_fin:
            try:
                filters['opDate__range'] = [fecha_inicio, fecha_fin]
            except ValueError:
                pass

        # Resto de filtros tradicionales
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