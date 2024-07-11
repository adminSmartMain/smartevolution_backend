# REST Framework imports
from rest_framework.decorators import APIView
# Utils
from apps.base.utils.index import response, pdfToBase64
from apps.report.utils.index import generateSellOfferByInvestor
from django.template.loader import get_template
import requests
# Decorators
from apps.base.decorators.index import checkRole

class SellOrderAV(APIView):

    @checkRole(['admin'])
    def post(self, request, pk=None):
        try:
            sellOffer = generateSellOfferByInvestor(request.data['opId'],request.data['investorId'])
            #gen the report
            template       = get_template('newBuyOrderSignatureTemplate.html')
            parsedTemplate = template.render(sellOffer)
            pdf            = pdfToBase64(parsedTemplate)
            return response({'error': False, 'data': {'pdf': pdf['pdf'], 'xd':sellOffer['payers']}}, 200)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
