# REST Framework imports
from rest_framework.decorators import APIView
# Serializers
from apps.administration.api.serializers.deposit.index import DepositReadOnlySerializer
# Utils
from apps.base.utils.index import response, numberToLetters, pdfToBase64
from django.template.loader import get_template
import requests
# Decorators
from apps.base.decorators.index import checkRole
# Models
from apps.administration.models import Deposit

class EgressReceiptAV(APIView):
    def post(self, request,pk):
        #get the deposit
        deposit = Deposit.objects.get(pk=pk)
        serializer = DepositReadOnlySerializer(deposit)
        data = {
        'id': serializer.data['dId'],
        'amount': serializer.data['amount'],
        'amount_text': numberToLetters(serializer.data['amount']),
        'date': serializer.data['date'],
            }
        template = get_template('egressReceipt.html')
        parsedTemplate = template.render(data)
        pdf = pdfToBase64(parsedTemplate)
        return response({'error': False, 'data': {'pdf': pdf['pdf'], 'dict':data}}, 200)