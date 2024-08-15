from django.db.models import Q
# Serializers
from apps.bill.api.serializers.index import BillSerializer, BillReadOnlySerializer, BillEventReadOnlySerializer
from apps.operation.api.serializers.index import PreOperationReadOnlySerializer
# Models
from apps.bill.models import Bill
from apps.client.models import Client
from apps.operation.models import PreOperation
# Utils
from apps.base.utils.index import response, BaseAV, gen_uuid
from apps.bill.utils.index import parseBill, parseCreditNote
from apps.base.decorators.index import checkRole
from base64 import b64decode
import os
import logging

class BillAV(BaseAV):
    @checkRole(['admin','third'])
    def post(self, request):
        try:
            data = []
            failedBills = []
            for x in request.data['bills']:
                # check if the request has a integrationCode

                if 'integrationCode' in x:
                    if x['integrationCode'] != "" or x['integrationCode'] != None:
                        if x['cufe'] == None or x['cufe'] == "":
                            failedBills.append({
                                'bill':x,
                                'error':'Factura sin cufe'
                            })
                        elif x['cufe'] != None or x['cufe'] != "":
                            # check if the bill is already registered by his cufe
                            checkBill = Bill.objects.filter(cufe=x['cufe'])

                            if len(checkBill) > 0:
                                failedBills.append({
                                'bill':x,
                                'error':'Factura con cufe registrado'
                                })
                            else:
                                data.append(x)
                        else:
                            data.append(x)
                else:
                    data.append(x)

            if len(failedBills) > 0:
                return response({'error': False, 'message': 'Algunas facturas presentan errores', 'bills': data, 'failedBills':failedBills}, 400)
            else:
                # save the bills
                for row in data:
                    request.data['creditNotes'] = row['creditNotes'] if 'creditNotes' in row else []
                    request.data['events'] = row['events'] if 'events' in row else []
                    # check if the dateBill, datePayment and expirationDate has the correct format it must be YYYY-MM-DDbut if the dateBill is in format YYYY-MM-DDT00:00:00 parse it to YYYY-MM-DD
                    if 'dateBill' in row:
                        if 'T' in row['dateBill']:
                            row['dateBill'] = row['dateBill'].split('T')[0]
                    if 'datePayment' in row:
                        if 'T' in row['datePayment']:
                            row['datePayment'] = row['datePayment'].split('T')[0]
                    if 'expirationDate' in row:
                        if 'T' in row['expirationDate']:
                            row['expirationDate'] = row['expirationDate'].split('T')[0]
                    serializer = BillSerializer(data=row, context={'request': request})
                    if serializer.is_valid():
                        serializer.save()
                    else:
                        return response({'error': True, 'message': serializer.errors}, 400)
                return response({'error': False, 'message': 'Facturas creadas',  'failedBills':failedBills}, 201)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)

    @checkRole(['admin','third'])
    def get(self, request, pk=None):
        try:

            if len(request.query_params) > 0:
                if request.query_params.get('emitter') != None:
                    bills = Bill.objects.filter(emitterName__icontains=request.query_params.get('emitter'))
                elif request.query_params.get('payer') != None:
                    bills = Bill.objects.filter(payerName__icontains=request.query_params.get('payer'))
                elif request.query_params.get('opId') != None:
                    billList = []
                    # get the bills of the operation
                    # get the opId
                    opId = PreOperation.objects.get(id=request.query_params.get('opId'))
                    op   = PreOperation.objects.filter(opId=opId.opId)
                    for x in op:
                        bills = Bill.objects.get(id=x.bill.id)
                        billList.append({
                            'id': bills.id,
                            'billId': bills.billId,
                            'total': bills.total,
                            'opAmount': x.payedAmount,
                            'opExpiration':x.opExpiration,
                            'dateBill': x.opDate
                        })                   
                    return response({'error': False, 'data': billList}, 200)

                elif request.query_params.get('bill') != None:
                    bills = Bill.objects.filter(billId__icontains=request.query_params.get('bill'))
                
                elif request.query_params.get('operation') != None:
                    billList = []
                    # get the bills of the operation
                    op   = PreOperation.objects.filter(opId=request.query_params.get('operation'))
                    for x in op:
                        bill = Bill.objects.get(id=x.bill.id)
                        billList.append(bill)
                    page       = self.paginate_queryset(billList)
                    if page is not None:
                        serializer = BillReadOnlySerializer(page, many=True)
                        return self.get_paginated_response(serializer.data)
                elif request.query_params.get('payerId') != None:
                    # get the payer of the bill
                    try:
                        bill   = Bill.objects.get(id=request.query_params.get('payerId'))
                        client = Client.objects.get(document_number=bill.payerId)
                        return response({'error': False, 'data': client.id}, 200)
                    except:
                        return response({'error': True, 'message': 'Pagador no Registrado'}, 400)

                elif request.query_params.get('reBuy') != None:
                    bill = PreOperation.objects.filter(bill_id=request.query_params.get('reBuy')).order_by('-opId').first()
                    serializer = PreOperationReadOnlySerializer(bill)
                    return response({'error': False, 'data': serializer.data}, 200)
                
                elif request.query_params.get('billEvent') != None:
                    # Get the bill
                    bill = Bill.objects.get(id=request.query_params.get('billEvent'))
                    if bill.cufe:
                        serializer = BillEventReadOnlySerializer(bill)
                        return response({'error': False, 'data':serializer.data}, 200)
                    else:
                        serializer = BillReadOnlySerializer(bill)
                        return response({'error': True, 'data': serializer.data}, 200)
                else:
                    bills = Bill.objects.filter(state=1)
                page       = self.paginate_queryset(bills)
                if page is not None:
                    serializer = BillReadOnlySerializer(page, many=True)
                    return self.get_paginated_response(serializer.data)


            if pk:
                client = Client.objects.get(pk=pk)
                bill = Bill.objects.filter(
                    Q(emitterId=pk) | Q(emitterId=client.document_number))
                serializer = BillReadOnlySerializer(bill, many=True)
                return response({'error': False, 'data': serializer.data}, 200)
            else:
                bills = Bill.objects.filter(state=1)
                page       = self.paginate_queryset(bills)
                if page is not None:
                    serializer = BillReadOnlySerializer(page, many=True)
                    return self.get_paginated_response(serializer.data)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)

    @checkRole(['admin'])
    def patch(self, request, pk):
        try:
            bill = Bill.objects.get(pk=pk)
            serializer = BillSerializer(bill, data=request.data, context={
                                        'request': request}, partial=True)
            if serializer.is_valid():
                serializer.save()
                return response({'error': False, 'message': 'Factura actualizada', 'data': serializer.data}, 200)
            else:
                return response({'error': True, 'data': serializer.errors}, 400)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)

    @checkRole(['admin'])
    def delete(self, request, pk):
        try:
            # verify if the bill is in an operation
            op = PreOperation.objects.filter(bill=pk)
            if len(op) > 0:
                return response({'error': True, 'message': 'La factura no se puede eliminar porque esta en una operacion'}, 400)
            else:
                bill = Bill.objects.get(pk=pk)
                bill.delete()
            return response({'error': False, 'message': 'Factura eliminada'}, 200)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)


class readBillAV(BaseAV):
    @checkRole(['admin','third'])
    def post(self, request):
        parsedBills = []
        duplicatedBills = []
        failedBills = []
        #try:
        for file in request.data['bills']:      
            # decode base 64 file
            # if file has data:text/xml;base64, remove it
            if file.startswith('data:text/xml;base64,'):
                file = file.replace('data:text/xml;base64,', '')
            fileName = f'{gen_uuid()}.xml'
            xmlData = b64decode(file, validate=True).decode('utf-8')
            with open(fileName, 'w') as f:
                f.write(xmlData)
            parseXml = parseBill(fileName)
            parseXml['file'] = file
            # add the data:text/xml;base64, to the file
            parseXml['file'] = f'data:text/xml;base64,{file}'
            os.remove(fileName)

            logging.log(logging.INFO, parseXml)
            # check if the bill has cufe
            if parseXml['cufe'] == "" or parseXml == None:
                failedBills.append(parseXml)
            else:
                # validate if the bill is duplicated
                bill = Bill.objects.filter(cufe=parseXml['cufe'])
                if len(bill) > 0:
                    duplicatedBills.append(parseXml)
                else:
                    parsedBills.append(parseXml)

        return response({'error': False, 'bills': parsedBills, 'duplicatedBills': duplicatedBills, 'failedBills':failedBills}, 200)    
        #except Exception as e:
        #    return response({'error': True, 'message': str(e)}, 500)


class readCreditNoteAV(BaseAV):
    @checkRole(['admin','third'])
    def post(self, request):
        parsedCreditNotes = []
        for file in request.FILES.getlist('creditNotes'):
            parsedCreditNotes.append(parseCreditNote(file))
        return response({'error': False, 'data': parsedCreditNotes}, 200)

