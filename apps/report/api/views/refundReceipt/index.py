# REST Framework imports
from rest_framework.decorators import APIView
# Serializers
from apps.administration.api.serializers.index import RefundReadOnlySerializer
# Utils
from apps.base.utils.index import response, numberToLetters
from django.template.loader import get_template
import requests
# Decorators
from apps.base.decorators.index import checkRole
# Models
from apps.administration.models import Refund

class RefundReceiptAV(APIView):
    def post(self, request, pk):
        try:
            refund = Refund.objects.get(pk=pk)
            serializer = RefundReadOnlySerializer(refund)
            data = {
            'id': serializer.data['rId'],
            'amount': serializer.data['amount'],
            'amount_text': numberToLetters(serializer.data['amount']),
            'date': serializer.data['date'],
            'client': serializer.data['client']['social_reason'] if serializer.data['client']['social_reason']  else serializer.data['client']['first_name'] + ' ' + serializer.data['client']['last_name'],
            'document': serializer.data['client']['document_number'],
            'beneficiary': serializer.data['beneficiary'],
            'bank': serializer.data['bank']['description'],
            'account': serializer.data['accountType']['description'] + '  -  ' + serializer.data['accountNumber'],
            }
            template = get_template('refundReceipt.html')
            test = template.render(data)
            pdf = requests.post(
                'https://j2ncm3xeo7.execute-api.us-east-1.amazonaws.com/dev/api/html-to-pdf', json={'html': test})
            return response({'error': False, 'data': {'pdf': pdf.json()['pdf'], 'dict':data}}, 200)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, 500)