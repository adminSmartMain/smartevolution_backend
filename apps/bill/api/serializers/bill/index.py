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
from django.conf import settings
# Exceptions
from apps.base.exceptions import HttpException


class BillSerializer(serializers.ModelSerializer):

    class Meta:
        model = Bill
        fields = '__all__'
    
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
    class Meta:
        model        = Bill
        fields       = '__all__'
        extra_fields = ['creditNotes']

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
        
    