# Rest Framework
from rest_framework import serializers
# Models
from apps.bill.models import Bill, CreditNote, BillEvent
from apps.operation.models import PreOperation
from apps.misc.models import TypeEvent
from apps.client.models import Client
# Serializers
from apps.bill.api.serializers.creditNote.index import CreditNoteSerializer
from apps.bill.api.serializers.event.index import BillEventSerializer
# Utils
from datetime import datetime as dt
from apps.base.utils.index import gen_uuid, PDFBase64File, uploadFileBase64
from apps.bill.utils.billEvents import billEvents
from apps.bill.utils.index import billEvents as updateBillEvents
import uuid
from django.conf import settings
# Exceptions
from apps.base.exceptions import HttpException
import boto3
from boto3.session import Session
from botocore.exceptions import ClientError
import logging
import base64
from base64 import b64decode
from django.core.cache import cache
from rest_framework.exceptions import ValidationError
# Configurar el logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)



def delete_old_file_from_s3(file_url):
    """
    Elimina un archivo antiguo de S3 dado su URL completo.
    """
    try:
        bucket = settings.AWS_STORAGE_BUCKET_NAME
        # Extraer la clave del archivo desde la URL
        if f's3.amazonaws.com/{bucket}/' in file_url:
            key = file_url.split(f's3.amazonaws.com/{bucket}/')[-1]
        elif f'{bucket}.s3.amazonaws.com/' in file_url:
            key = file_url.split(f'{bucket}.s3.amazonaws.com/')[-1]
        else:
            key = file_url.split(f'{bucket}/')[-1]
        s3 = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=getattr(settings, 'AWS_REGION', getattr(settings, 'AWS_REGION', None))
        )
        s3.delete_object(Bucket=bucket, Key=key)
    except Exception as e:
        logger.warning(f"Error deleting old file from S3: {e}")

# Crear un handler de consola y definir el nivel
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# Crear un formato para los mensajes de log
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

# Añadir el handler al logger
logger.addHandler(console_handler)
##comentario2

class BillCreationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bill
        fields = [
            'typeBill', 'billId', 'emitterId', 
            'currentBalance', 'dateBill', 'expirationDate',
            'payerName', 'payerId', 'emitterName', 'datePayment','billValue','subTotal','total','file','ret_iva','ret_ica'
            ,'ret_fte','other_ret'
        ]

        
    def validate_billId(self, value):
        """
        Validación personalizada para billId duplicado
        """
        if Bill.objects.filter(billId=value).exists():
            raise serializers.ValidationError("Este ID de factura ya está registrado")
        return value
    def create(self, validated_data):
        try:
            # Usar el usuario del request
            validated_data['id'] = gen_uuid()
            validated_data['user_created_at'] = self.context['request'].user
            # upload the bill to s3
            if 'file' in validated_data:
                fileUrl = validated_data.get('file', None)
                if fileUrl:
                    fileUrl = uploadFileBase64(files_bse64=[fileUrl], file_path=f'bill/{validated_data["id"]}')
                    validated_data['file'] = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/{fileUrl}"
            # Si necesitas igualar currentBalance con total
            if 'currentBalance' in validated_data:
                validated_data['currentBalance'] = validated_data['currentBalance']
            
            # Crear la factura
            bill = Bill.objects.create(**validated_data)
            return bill
            
        except Exception as e:
            logger.error(f"Error al crear factura: {str(e)}")
            raise serializers.ValidationError(str(e))
class BillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bill
        fields = '__all__'
        extra_kwargs = {
            'id': {
                'required': False,
                'read_only': False  # Permitir asignación manual
            }
        }

    def create(self, validated_data):
        try:
            validated_data['id'] = gen_uuid()
            validated_data['user_created_at'] = self.context['request'].user
            validated_data['currentBalance']  = validated_data['total']
            
            # upload the bill to s3
            if 'file' in validated_data:
                fileUrl = validated_data.get('file', None)
                if fileUrl:
                    fileUrl = uploadFileBase64(files_bse64=[fileUrl], file_path=f'bill/{validated_data["id"]}')
                    validated_data['file'] = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/{fileUrl}"
            # save the bill
            bill = Bill.objects.create(**validated_data)
            # save the credit notes
            if 'creditNotes' in self.context['request'].data:
                for creditNote in self.context['request'].data['creditNotes']:
                    creditNote['id'] = gen_uuid()
                    creditNote['user_created_at'] = self.context['request'].user
                    creditNote['Bill'] = bill
                    CreditNote.objects.create(**creditNote)
            # save the events
            if 'events' in self.context['request'].data:
                for event in self.context['request'].data['events']:
                    event['user_created_at'] = self.context['request'].user
                    event['Bill'] = bill
                    BillEvent.objects.create(
                        id = gen_uuid(),
                        user_created_at = self.context['request'].user,
                        bill     = bill,
                        event_id = event['event'],
                        date=event['date']
                    )
            return validated_data
        except Exception as e:
            raise HttpException(500, e)

    def update(self, instance, validated_data):
        instance.updated_at = dt.now()
        instance.user_updated_at = self.context['request'].user
        
        if 'file' in validated_data:
            file_data = validated_data.get('file')
            
            # Solo procesar si es un nuevo archivo base64
            if file_data and isinstance(file_data, str) and file_data.startswith('data:'):
                try:
                    # Extraer el tipo de archivo del prefijo base64
                    file_type = file_data.split(';')[0].split('/')[-1]
                    if file_type not in ['pdf', 'jpeg', 'png']:
                        raise ValidationError("Formato de archivo no soportado")
                    
                    # Subir a S3 usando el ID de la instancia
                    file_key = uploadFileBase64(
                        files_bse64=[file_data], 
                        file_path=f'bills/{instance.id}'  # Usar instance.id
                    )
                    
                    if not file_key:
                        raise ValueError("Error al subir archivo a S3")
                    
                    validated_data['file'] = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/{file_key}"
                    
                    # Opcional: Eliminar archivo antiguo si existe
                    if instance.file:
                        try:
                            # Implementar esta función según tu SDK de AWS
                            delete_old_file_from_s3(instance.file)
                        except Exception as delete_error:
                            logger.warning(f"No se pudo eliminar archivo antiguo: {delete_error}")
                            
                except Exception as upload_error:
                    logger.error(f"Error subiendo archivo: {upload_error}")
                    # Mantener el archivo existente si falla la subida
                    validated_data['file'] = instance.file
                    # O alternativamente: del validated_data['file']
        
        return super().update(instance, validated_data)


class BillReadOnlySerializer(serializers.ModelSerializer):
    creditNotes          = serializers.SerializerMethodField(method_name='get_creditNotes')
    associatedOperation  = serializers.SerializerMethodField(method_name='get_associatedBill')
    sameCurrentOwner     = serializers.SerializerMethodField(method_name='get_sameCurrentOwner')
    endorsedBill         = serializers.SerializerMethodField(method_name='get_endorsedBill')
    currentOwnerName     = serializers.SerializerMethodField(method_name='get_currentOwnerName')
    emitterIdOperation   = serializers.SerializerMethodField(method_name='get_emitter_id')
    file_content = serializers.SerializerMethodField(method_name='get_file_content')
    file_content_type = serializers.SerializerMethodField(method_name='get_file_content_type')
    class Meta:
        model        = Bill
        fields       = '__all__'
        extra_fields = ['creditNotes','file_content', 'file_content_type']
        
    


    def get_file_content(self, obj):
        if not obj.file:
            return None
        
        # Verificar en cache si ya sabemos que este archivo no existe
        cache_key = f"missing_file_{obj.id}"
        if cache.get(cache_key):
            return None
            
        try:
            s3 = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION
            )
            
            bucket = settings.AWS_STORAGE_BUCKET_NAME
            s3_url = obj.file
            
            # Extracción robusta de la key
            key = None
            patterns = [
                f's3.amazonaws.com/{bucket}/',
                f'{bucket}.s3.amazonaws.com/',
                f'{bucket}/'
            ]
            
            for pattern in patterns:
                if pattern in s3_url:
                    key = s3_url.split(pattern)[-1]
                    break
                    
            if not key:
                logger.warning(f"Formato de URL S3 no reconocido para bill {obj.id}")
                return None
                
            # Verificar primero si el objeto existe antes de intentar leerlo
            try:
                s3.head_object(Bucket=bucket, Key=key)
            except s3.exceptions.NoSuchKey:
                # Registrar en cache que este archivo no existe (por 24 horas)
                cache.set(cache_key, True, timeout=86400)
                logger.warning(f"Archivo no encontrado en S3 para bill {obj.id}, key: {key}")
                return None
            except Exception as e:
                logger.error(f"Error verificando archivo para bill {obj.id}: {str(e)}")
                return None
                
            # Si llegamos aquí, el archivo existe, proceder a leerlo
            response = s3.get_object(
                Bucket=bucket,
                Key=key,
                RequestPayer='requester'
            )
            
            max_size = 20 * 1024 * 1024
            file_bytes = response['Body'].read(amt=max_size)
            
            if len(file_bytes) == max_size:
                remaining_bytes = response['Body'].read()
                if remaining_bytes:
                    raise ValueError("El archivo excede el tamaño máximo permitido")
                    
            return base64.b64encode(file_bytes).decode('utf-8')
            
        except Exception as e:
            logger.error(f"Error obteniendo archivo para bill {obj.id}: {str(e)}")
            return None
                

    def get_file_content_type(self, obj):
        if not obj.file:
            return None
            
        if obj.file.lower().endswith('.pdf'):
            return 'application/pdf'
        elif obj.file.lower().endswith(('.jpg', '.jpeg')):
            return 'image/jpeg'
        elif obj.file.lower().endswith('.png'):
            return 'image/png'
        else:
            return 'application/octet-stream'

    def get_creditNotes(self, obj):
        creditNotes = CreditNote.objects.filter(Bill=obj)
        return CreditNoteSerializer(creditNotes, many=True).data

    def get_associatedBill(self, obj):
        try:
            op = PreOperation.objects.filter(bill=obj).order_by('-created_at')
            payedAmount = 0
            for row in op:
                payedAmount+=row.payedAmount
                
            return { 'opId': op[0].opId, 'payedAmount':payedAmount }
        except Exception as e:
            return None
        
    def get_sameCurrentOwner(self, obj):
        try:
            return False
        except:
            return False
    
    def get_endorsedBill(self, obj):
        try:
            return False
        except:
            return False

    def get_currentOwnerName(self, obj):
        try:
            return None
        except:
            return None
        
    def get_emitter_id(self, obj):
        try:
            return Client.objects.get(document_number=obj.emitterId).id
        except:
            return None
        


class BillEventReadOnlySerializer(serializers.ModelSerializer):
    creditNotes          = serializers.SerializerMethodField(method_name='get_creditNotes')
    associatedOperation  = serializers.SerializerMethodField(method_name='get_associatedBill')
    sameCurrentOwner     = serializers.SerializerMethodField(method_name='get_sameCurrentOwner')
    endorsedBill         = serializers.SerializerMethodField(method_name='get_endorsedBill')
    currentOwnerName     = serializers.SerializerMethodField(method_name='get_currentOwnerName')
    events               = serializers.SerializerMethodField(method_name='get_events')
    file_presigned_url   = serializers.SerializerMethodField(method_name='get_file_presigned_url')
    file_access_error    = serializers.SerializerMethodField(method_name='get_file_access_error') 
    
    class Meta:
        model        = Bill
        fields       = '__all__'
        extra_fields = ['creditNotes','file_presigned_url', 'file_access_error']
        
    
        
    def get_file_presigned_url(self, obj):
        if not obj.file:
            return None
            
        try:
            # Extraer la clave S3 de la URL completa
            s3_url = obj.file
            key = s3_url.split('devsmartevolution.s3.amazonaws.com/')[-1]
            
            s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION
            )
            
            # Generar URL pre-firmada válida por 1 hora
            presigned_url = s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                    'Key': key
                },
                ExpiresIn=3600
            )
            return presigned_url
        except Exception as e:
            logger.error(f"Error generating presigned URL for bill {obj.id}: {str(e)}")
            return None

    def get_file_access_error(self, obj):
        if not obj.file:
            return None
        try:
            # Verificar si podemos generar la URL
            url = self.get_file_presigned_url(obj)
            return not bool(url)
        except:
            return True
        
        
    def get_creditNotes(self, obj):
        creditNotes = CreditNote.objects.filter(Bill=obj)
        return CreditNoteSerializer(creditNotes, many=True).data

    def get_associatedBill(self, obj):
        try:
            op = PreOperation.objects.filter(bill=obj).order_by('-created_at')
            payedAmount = 0
            for row in op:
                payedAmount+=row.payedAmount
                
            return { 'opId': op[0].opId, 'payedAmount':payedAmount }
        except:
            return None
        
    def get_sameCurrentOwner(self, obj):
        try:
            if obj.cufe is None:
                return False
            else:
                parse = billEvents(obj.cufe)
                # strip the current owner
                parse['currentOwner'] = parse['currentOwner'].strip()
                # check if the current owner is the same as the owner of the bill
                if parse['currentOwner'] == obj.emitterName:
                    return True
                else:
                    return False
        except:
            return False
    
    def get_endorsedBill(self, obj):
        try:
            if obj.cufe is None:
                return False
            else:
                parse = updateBillEvents(obj.cufe)
            # check if the bill has the event f5d475c0-4433-422f-b3d2-7964ea0aa5c4
                valid = False
                for event in parse:
                    if event['eventId'] == '3ea77762-7208-457a-b035-70069ee42b5e':
                        valid = True
                        break
                    if event['eventId'] == '3bb86c74-1d1c-4986-a905-a47624b09322':
                        valid = True
                        break
                    if event['eventId'] == '0e333b6b-27b1-4aaf-87ce-ad60af6e52e6':
                        valid = True
                        break
            for x in parse:
                try:
                    eventId = TypeEvent.objects.get(id=x['eventId'])
                    event   = BillEvent.objects.get(bill=obj, event=eventId)
                except:
                    eventId = TypeEvent.objects.get(id=x['eventId'])
                    BillEvent.objects.create(id=gen_uuid(), bill=obj, event=eventId, date=x['date'])
                
                if valid:
                    return True
                else:
                    return False 
        except:
            return False

    def get_currentOwnerName(self, obj):
        try:
            if obj.cufe is None:
                return None
            else:
                parse = billEvents(obj.cufe)
                # strip the current owner
                parse['currentOwner'] = parse['currentOwner'].strip()
                # check if the current owner is the same as the owner of the bill
                return parse['currentOwner']
        except:
            return None
        
    def get_events(self, obj):
        events = []
        try:
            if obj.cufe:
                checkEvents = billEvents(obj.cufe, True)
                # check if the bill has the detected events
                for x in checkEvents['events']:
                    try:
                        eventId = TypeEvent.objects.get(id=x['event'])
                        event   = BillEvent.objects.get(bill=obj, event=eventId)
                    except:
                        eventId = TypeEvent.objects.get(id=x['event'])
                        BillEvent.objects.create(id=gen_uuid(), bill=obj, event=eventId, date=x['date'])
                # get the events of the bill
                checkBillEvents = BillEvent.objects.filter(bill=obj)
                for x in checkBillEvents:
                    events.append({
                        'event': x.event.description,
                        'date': x.date,
                        'code': x.event.code
                    })
                return events
            else:
                return []
        except:
            return []
        
    