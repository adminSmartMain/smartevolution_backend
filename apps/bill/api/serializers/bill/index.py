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
from django.db import transaction
from django.core.exceptions import ValidationError

from apps.base.exceptions import HttpException
from apps.bill.api.models.bill.index import Bill
from apps.bill.api.models.event.index import BillEvent
from apps.misc.api.models.typeEvent.index import TypeEvent# ajusta imports

from apps.bill.utils.events import normalize_description  # ajusta a tu ruta

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
            'payerName', 'payerId', 'emitterName', 'datePayment','billValue','subTotal','total','file','ret_iva','ret_ica','iva'
            ,'ret_fte','other_ret'
        ]

        
    def validate_billId(self, value):
        """
        Validación personalizada para billId duplicado por emisor
        """
        # Obtener el emitterId del contexto de los datos
        emitter_id = self.initial_data.get('emitterId')
        emitterName=self.initial_data.get('emitterName')
      
        if not emitter_id:
            raise serializers.ValidationError("El campo emitterId es requerido para la validación")
        
        # Verificar si ya existe una factura con el mismo billId y emitterId
        if Bill.objects.filter(billId=value, emitterId=emitter_id).exists():
            raise serializers.ValidationError(
                f"El ID de factura '{value}' ya está registrado para el emisor '{emitterName}'"
            )
        
        return value

    def create(self, validated_data):
        try:
            # Usar el usuario del request
            validated_data['id'] = gen_uuid()
            validated_data['user_created_at'] = self.context['request'].user
            
            # Subir el archivo a S3
            if 'file' in validated_data:
                fileUrl = validated_data.get('file', None)
                if fileUrl:
                    fileUrl = uploadFileBase64(
                        files_bse64=[fileUrl], 
                        file_path=f'bill/{validated_data["id"]}'
                    )
                    validated_data['file'] = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/{fileUrl}"
            
            # Asegurar que currentBalance sea igual a total si no se especifica
            if 'currentBalance' not in validated_data:
                validated_data['currentBalance'] = validated_data.get('total', 0)
            elif validated_data.get('total'):
                validated_data['currentBalance'] = validated_data['total']
            
            # Crear la factura
            bill = Bill.objects.create(**validated_data)
            return bill
            
        except Exception as e:
            logger.error(f"Error al crear factura: {str(e)}")
            raise serializers.ValidationError(f"Error al crear la factura: {str(e)}")
            
        
        
class BillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bill
        fields = '__all__'
        extra_kwargs = {
            'id': {'required': False, 'read_only': False}
        }

    @transaction.atomic
    def create(self, validated_data):
        try:
            validated_data['id'] = gen_uuid()
            validated_data['user_created_at'] = self.context['request'].user
            validated_data['currentBalance'] = validated_data['total']

            # upload the bill to s3
            if 'file' in validated_data:
                fileUrl = validated_data.get('file', None)
                if fileUrl:
                    fileUrl = uploadFileBase64(
                        files_bse64=[fileUrl],
                        file_path=f'bill/{validated_data["id"]}'
                    )
                    validated_data['file'] = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/{fileUrl}"

            bill = Bill.objects.create(**validated_data)

            # credit notes
            if 'creditNotes' in self.context['request'].data:
                for creditNote in self.context['request'].data['creditNotes']:
                    creditNote['id'] = gen_uuid()
                    creditNote['user_created_at'] = self.context['request'].user
                    creditNote['Bill'] = bill
                    CreditNote.objects.create(**creditNote)

            # events (NUEVO)
            raw_events = self.context['request'].data.get('events', [])
            if raw_events:
                for ev in raw_events:
                    code = (ev.get("code") or "").strip()
                    desc = (ev.get("description") or "").strip()
                    date = ev.get("date")

                    if not code:
                        # Si quieres ser estricto:
                        # raise ValidationError("Evento sin code")
                        continue

                    # normaliza descripción para comparar
                    desc_norm = normalize_description(desc)

                    # buscar TypeEvent existente por code y description (normalizada)
                    # Como en BD guardas description "original", la comparación la hacemos por igualdad normalizada.
                    # Opción simple: comparar por code exacto y description exacta.
                    # Mejor: guardar description normalizada también (pero ahora NO tienes ese campo).
                    #
                    # Solución sin tocar modelo:
                    candidates = TypeEvent.objects.filter(code=code)
                    found = None
                    
                    for t in candidates:
                        if normalize_description(t.supplierDescription) == desc_norm:
                            found = t
                            break

                    if not found:
                        found = TypeEvent.objects.create(
                            id=gen_uuid(),
                            user_created_at=self.context['request'].user,
                            code=code,
                            supplierDescription=desc,   # <-- aquí
                            dianDescription=""          # <-- opcional
                        )
                    # evitar duplicar BillEvent mismo bill + typeevent + date (opcional)
                    # Si tu negocio permite duplicados, quítalo.
                    if date:
                        exists = BillEvent.objects.filter(
                            bill=bill,
                            event=found,
                            date=date
                        ).exists()
                        if exists:
                            continue

                    BillEvent.objects.create(
                        id=gen_uuid(),
                        user_created_at=self.context['request'].user,
                        bill=bill,
                        event=found,
                        date=date
                    )

            return bill

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
                        file_path=f'bill/{instance.id}'  # Usar instance.id
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
    
    class Meta:
        model        = Bill
        fields       = '__all__'
        extra_fields = ['creditNotes']

    def to_representation(self, instance):
        # Agregar logs de depuración
        logger.debug(f"Serializando factura ID: {instance.id}")
        logger.debug(f"Factura payerId: {instance.payerId}, tipo: {type(instance.payerId)}")
        logger.debug(f"Factura emitterId: {instance.emitterId}, tipo: {type(instance.emitterId)}")
        
        data = super().to_representation(instance)
        
        # Agregar info de depuración al JSON
        data['_debug'] = {
            'payerId_value': instance.payerId,
            'payerId_type': str(type(instance.payerId)),
            'emitterId_value': instance.emitterId,
            'emitterId_type': str(type(instance.emitterId)),
        }
        
        return data

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
class BillDetailSerializer(BillReadOnlySerializer):
    file_content = serializers.SerializerMethodField(method_name='get_file_content')
    file_content_type = serializers.SerializerMethodField(method_name='get_file_content_type')

    class Meta(BillReadOnlySerializer.Meta):
        extra_fields = ['creditNotes', 'file_content', 'file_content_type']

    
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

class BillEventReadOnlySerializer(serializers.ModelSerializer):
    creditNotes          = serializers.SerializerMethodField(method_name='get_creditNotes')
    associatedOperation  = serializers.SerializerMethodField(method_name='get_associatedBill')
    sameCurrentOwner     = serializers.SerializerMethodField(method_name='get_sameCurrentOwner')
    endorsedBill         = serializers.SerializerMethodField(method_name='get_endorsedBill')
    currentOwnerName     = serializers.SerializerMethodField(method_name='get_currentOwnerName')
    currentOwnerId       = serializers.SerializerMethodField(method_name='get_currentOwnerId')
    events               = serializers.SerializerMethodField(method_name='get_events')
    file_presigned_url   = serializers.SerializerMethodField(method_name='get_file_presigned_url')
    file_access_error    = serializers.SerializerMethodField(method_name='get_file_access_error')

    # ⬅️ NUEVO: Campo "type" calculado desde billEvents()
    type = serializers.SerializerMethodField(method_name='get_type')

    class Meta:
        model  = Bill
        fields = '__all__'   # Enviaremos typeBill, pero modificado

    # ============================================================
    # 🔥 CACHE ÚNICO — UNA SOLA PETICIÓN POR FACTURA
    # ============================================================
    def _get_billEvents(self, obj):
        if not hasattr(self, "_cache_events"):
            self._cache_events = {}

        if obj.cufe not in self._cache_events:
            self._cache_events[obj.cufe] = billEvents(obj.cufe, update=True)

        return self._cache_events[obj.cufe]

    # ============================================================
    # TIPO REAL DE LA FACTURA (ENDOSADA / FV-TV / FV / RECHAZADA)
    # ============================================================
    def get_type(self, obj):
        try:
            if not obj.cufe:
                return None
            events = self._get_billEvents(obj)
            return events.get("type")   # UUID REAL según eventos
        except:
            return None

    # ============================================================
    # Sobrescribir JSON final del serializer
    # Reemplaza typeBill por el tipo REAL
    # ============================================================
    def to_representation(self, instance):
        data = super().to_representation(instance)

        # Sobrescribe typeBill con el valor REAL
        events = self._get_billEvents(instance)
        real_type = events.get("type")

        if real_type:
            data["typeBill"] = real_type  # <-- ahora SIEMPRE el valor correcto

        return data

    # ============================================================
    # FILE URL
    # ============================================================
    def get_file_presigned_url(self, obj):
        if not obj.file:
            return None
        try:
            s3_url = obj.file
            key = s3_url.split('devsmartevolution.s3.amazonaws.com/')[-1]

            s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION
            )

            return s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': settings.AWS_STORAGE_BUCKET_NAME, 'Key': key},
                ExpiresIn=3600
            )
        except Exception as e:
            logger.error(f"Error generating presigned URL for bill {obj.id}: {str(e)}")
            return None

    def get_file_access_error(self, obj):
        try:
            url = self.get_file_presigned_url(obj)
            return not bool(url)
        except:
            return True

    # ============================================================
    # CREDIT NOTES
    # ============================================================
    def get_creditNotes(self, obj):
        notes = CreditNote.objects.filter(Bill=obj)
        return CreditNoteSerializer(notes, many=True).data

    # ============================================================
    # ASSOCIATED OP
    # ============================================================
    def get_associatedBill(self, obj):
        try:
            ops = PreOperation.objects.filter(bill=obj).order_by('-created_at')
            payedAmount = sum(row.payedAmount for row in ops)
            return {'opId': ops[0].opId, 'payedAmount': payedAmount}
        except:
            return None

    # ============================================================
    # SAME CURRENT OWNER
    # ============================================================
    def get_sameCurrentOwner(self, obj):
        try:
            if not obj.cufe:
                return False
            events = self._get_billEvents(obj)
            owner = events.get("holderIdNumber", "").strip()
           
            return owner == obj.emitterId
        except:
            return False

    # ============================================================
    # CURRENT OWNER NAME
    # ============================================================
    def get_currentOwnerName(self, obj):
        try:
            if not obj.cufe:
                return None
            events = self._get_billEvents(obj)
            return events.get("currentOwner", "").strip()
        except:
            return None
        
    def get_currentOwnerId(self, obj):
        try:
            if not obj.cufe:
                return None
            events = self._get_billEvents(obj)
            return events.get("current_ownerId", "").strip()
        except:
            return None

    # ============================================================
    # EVENTS
    # ============================================================
    def get_events(self, obj):
        try:
            if not obj.cufe:
                return []

            api_resp = self._get_billEvents(obj)
            api_events = api_resp.get("events", []) or []

            for ev in api_events:
                code = (ev.get("code") or "").strip()
                supplier_desc = (ev.get("description") or "").strip()
                date = ev.get("date") or None

                if not code:
                    continue

                type_ev = None

                # 1) Si viene description, busca por code + supplierDescription(normalizada)
                if supplier_desc:
                    desc_norm = normalize_description(supplier_desc)
                    candidates = TypeEvent.objects.filter(code=code)
                    for t in candidates:
                        if normalize_description(t.supplierDescription) == desc_norm:
                            type_ev = t
                            break

                    # si no existe en catálogo, lo creas
                    if not type_ev:
                        type_ev = TypeEvent.objects.create(
                            id=gen_uuid(),
                            code=code,
                            supplierDescription=supplier_desc,
                            dianDescription="",
                        )

                # 2) Si NO viene description, usa catálogo por code
                else:
                    # Prioriza uno con dianDescription lleno, si existe
                    type_ev = (
                        TypeEvent.objects
                        .filter(code=code)
                        .exclude(dianDescription__isnull=True)
                        .exclude(dianDescription__exact="")
                        .first()
                    ) or TypeEvent.objects.filter(code=code).first()

                    # Si ni siquiera existe por code, ahí sí toca crearlo vacío
                    if not type_ev:
                        type_ev = TypeEvent.objects.create(
                            id=gen_uuid(),
                            code=code,
                            supplierDescription="",
                            dianDescription="",
                        )

                # 3) Persistir BillEvent
                if date:
                    BillEvent.objects.get_or_create(
                        bill=obj,
                        event=type_ev,
                        date=date,
                        defaults={'id': gen_uuid()}
                    )
                else:
                    BillEvent.objects.get_or_create(
                        bill=obj,
                        event=type_ev,
                        defaults={'id': gen_uuid(), 'date': None}
                    )

            final = BillEvent.objects.filter(bill=obj).select_related("event").order_by("date")

            return [
                {
                    "code": e.event.code,
                    "supplierDescription": e.event.supplierDescription or "",
                    "dianDescription": e.event.dianDescription or "",
                    "description": (e.event.dianDescription or e.event.supplierDescription or ""),
                    "date": e.date,
                }
                for e in final
            ]

        except Exception as e:
            logger.error(f"Error en get_events bill {obj.id}: {str(e)}", exc_info=True)
            return []


    # ============================================================
    # ENDORSED BILL (optimizado)
    # ============================================================
    def get_endorsedBill(self, obj):
        try:
            if not obj.cufe:
                return False

            events = self._get_billEvents(obj)
            api_events = events.get("events", [])

            valid_ids = {
                '3ea77762-7208-457a-b035-70069ee42b5e',
                '3bb86c74-1d1c-4986-a905-a47624b09322',
                '0e333b6b-27b1-4aaf-87ce-ad60af6e52e6'
            }

            has_valid = any(ev.get("event") in valid_ids for ev in api_events)

            return has_valid
        except:
            return False
