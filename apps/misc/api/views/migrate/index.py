# REST Framework imports
from rest_framework.generics import GenericAPIView
# Models
from apps.authentication.models import User
from apps.operation.models import PreOperation, Receipt
from apps.client.models import Broker, Client, LegalRepresentative, Account, RiskProfile, Assets, Passives, Patrimony, StateOfResult, FinancialProfile, Overview, FinancialCentral
from apps.misc.models import Department, City, TypeIdentity, TypeCLient, Country, CIIU, AccountType, Bank, TypePeriod, TypeBill, TypeOperation, TypeExpenditure, AccountingAccount, TypeReceipt, ReceiptStatus,Fixes
from apps.bill.models import Bill 
from apps.administration.models import EmitterDeposit, AccountingControl, Deposit, Refund
from apps.report.models import NegotiationSummary, PendingAccount
# Serializers
from apps.misc.api.serializers.index import DepartmentSerializer
from apps.operation.api.serializers.index import ReceiptSerializer, PreOperationReadOnlySerializer
from apps.operation.api.serializers.index import PreOperationSerializer
from apps.administration.api.serializers.index import RefundSerializer, DepositSerializer
from apps.report.utils.index import generateSellOfferByInvestor
from django.template.loader import get_template

# UtilsNegotiationSummary
from apps.base.utils.index import response, gen_uuid, pdfToBase64
import requests
from bs4 import BeautifulSoup
import re
import threading
from django.db.models import Sum
class MigrateAV(GenericAPIView):
    counter = 0
    multi = 0
    notFound = 0
    notFoundBill = []

    def process_chunk(self, chunk, chunkId):
        try:
            bills = []
            for x in chunk:
                # get the receipt
                receipt = Receipt.objects.get(id=x['id'])
                receipt.tableInterests = 0
                receipt.additionalInterestsSM = x['additionalInterestsSM']
                receipt.save()
                print('guardado sabes')
            #PreOperation.objects.bulk_create(bills)
        except Exception as e:
            print(e,'error')

                
    def post(self, request, pk=None):
        try:

            operations = request.data['data']
            counter = 0

            for x in operations:
                # get the operation
                try:
                    serializer = ReceiptSerializer(data=x)
                    if serializer.is_valid():
                        serializer.save()
                        counter += 1
                        print("guardado sabes ",counter)
                    else:
                        print(serializer.errors)
                except Exception as e:
                    print('no encontrada sabes ',e)


            #chunk    = 300
            #chunks   = [deposits[x:x+chunk] for x in range(0, length, chunk)]
            #threads  = []
            #for chunk in chunks:
            #    self.counter += 1
            #    thread = threading.Thread(target=self.process_chunk, args=(chunk,f'chunk-{self.counter}'))
            #    thread.start()
            #    threads.append(thread)
            ## Esperar a que todos los hilos terminen
            #for thread in threads:
            #    thread.join()
            return response({'error': False, }, 200)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
        
    def get(self, request):
        return response({'error': False, 'data':'migrado exitosamente'}, 200)