# REST Framework imports
from rest_framework.decorators import APIView
# Serializers
from apps.administration.api.serializers.index import RefundReadOnlySerializer
from apps.base.utils.index import response, BaseAV, gen_uuid, pdfToBase64
# Utils
from apps.base.utils.index import response, numberToLetters
from django.template.loader import get_template
import requests
# Decorators
from apps.base.decorators.index import checkRole
# Models
from apps.administration.models import Refund
import logging

# Configurar el logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Crear un handler de consola y definir el nivel
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# Crear un formato para los mensajes de log
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

# Añadir el handler al logger
logger.addHandler(console_handler)

class RefundReceiptAV(APIView):
    def post(self, request, pk):
        try:
            logger.debug(f'Iniciando generación de recibo para reembolso ID: {pk}')
            
            # Obtener el reembolso
            refund = Refund.objects.get(pk=pk)
            serializer = RefundReadOnlySerializer(refund)
            refund_data = serializer.data
            
            logger.debug(f'Reembolso encontrado: {refund_data["rId"]}')
            
            # Preparar datos para el template con manejo seguro
            client_data = refund_data.get('client', {})
            bank_data = refund_data.get('bank', {})
            account_type_data = refund_data.get('accountType', {})
            
            client_name = (client_data.get('social_reason') or 
                          f"{client_data.get('first_name', '')} {client_data.get('last_name', '')}".strip())
            
            data = {
                'id': refund_data.get('rId', ''),
                'amount': refund_data.get('amount', 0),
                'amount_text': numberToLetters(refund_data.get('amount', 0)),
                'date': refund_data.get('date', ''),
                'client': client_name,
                'document': client_data.get('document_number', ''),
                'beneficiary': refund_data.get('beneficiary', ''),
                'bank': bank_data.get('description', ''),
                'account': f"{account_type_data.get('description', '')}  -  {refund_data.get('accountNumber', '')}",
            }
            
            logger.debug('Datos preparados para el template')
            
            # Renderizar template
            template = get_template('refundReceipt.html')
            html_content = template.render(data)
            logger.debug(f'Template renderizado, longitud HTML: {len(html_content)}')
            
            # Convertir HTML a PDF
            parseBase64 = pdfToBase64(html_content)
            
            # Verificar que la respuesta tenga la estructura esperada
            if 'pdf' in parseBase64:
                pdf_base64 = parseBase64['pdf']
                logger.debug('PDF generado exitosamente')
                
                return response({
                    'error': False, 
                    'pdf': pdf_base64,
                    'data': data
                }, 200)
            else:
                logger.error(f"Estructura inesperada en parseBase64: {parseBase64}")
                return response({
                    'error': True, 
                    'message': 'Formato de PDF incorrecto'
                }, 500)
            
        except Refund.DoesNotExist:
            logger.error(f'Reembolso no encontrado con ID: {pk}')
            return response({
                'error': True, 
                'message': 'Reembolso no encontrado'
            }, 404)
            
        except KeyError as e:
            logger.error(f'Falta dato requerido en la estructura: {str(e)}')
            return response({
                'error': True, 
                'message': f'Dato faltante en la estructura: {str(e)}'
            }, 500)
            
        except Exception as e:
            logger.error(f"Error inesperado generando recibo: {str(e)}")
            return response({
                'error': True, 
                'message': f'Error al generar recibo: {str(e)}'
            }, 500)