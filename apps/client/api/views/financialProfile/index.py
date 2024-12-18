# REST Framework imports
from rest_framework.decorators import APIView
# Models
from apps.client.models import FinancialProfile, Overview,Client, FinancialCentral
from apps.misc.models import Bank
# Serializers
from apps.client.api.serializers.index import (FinancialProfileSerializer, AssetsSerializer, PassivesSerializer,
                                                PatrimonySerializer, StateOfResultSerializer, OverviewSerializer,
                                                FinancialProfileReadOnlySerializer, FinancialCentralSerializer,
                                                FinancialCentralReadOnlySerializer, FinancialProfileUpdateSerializer)
# Utils
from apps.base.utils.index import response, gen_uuid, pdfToBase64
from apps.report.utils.index import calcReportVariability
from django.utils.translation import gettext as _
from datetime import datetime as dt
from django.template.loader import get_template
import requests
# Decorators
from apps.base.decorators.index import checkRole
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

class FinancialProfileAV(APIView):
    
    @checkRole(['admin'])
    def post(self, request):
        try:            
            financialProfiles = []
            errors            = []
            for x in range(len(request.data['periods'])):
                # validate if the period already exists
                if FinancialProfile.objects.filter(client=request.data['periods'][x]['client'], period=request.data['periods'][x]['period']).exists():
                    return response({'error': True, 'message': 'este periodo ya se encuentra registrado - {}'.format(request.data['periods'][x]['period'])}, 400)
                # save assets
                assets = AssetsSerializer(data=request.data['periods'][x]['assets'], context={'request': request})
                if assets.is_valid():
                    assets.save()
                else:
                    errors.append(assets.errors)
                # save passives
                passives = PassivesSerializer(data=request.data['periods'][x]['passives'], context={'request': request})
                if passives.is_valid():
                    passives.save()
                else:
                    errors.append(passives.errors)
                # save patrimony
                patrimony = PatrimonySerializer(data=request.data['periods'][x]['patrimony'], context={'request': request})
                if patrimony.is_valid():
                    patrimony.save()
                else:
                    errors.append(patrimony.errors)
                # save state of result
                stateOfResult = StateOfResultSerializer(data=request.data['periods'][x]['stateOfResult'], context={'request': request})
                if stateOfResult.is_valid():
                    stateOfResult.save()
                else:
                    errors.append(stateOfResult.errors)

                # append financial profile
                financialProfiles.append({
                'period'                      : request.data['periods'][x]['period'],
                'client'                      : request.data['periods'][x]['client'],
                'typePeriod'                  : request.data['periods'][x]['typePeriod'],
                'balance'                     : request.data['periods'][x]['balance'],
                'stateOfCashflow'             : request.data['periods'][x]['stateOfCashflow'],
                'financialStatementAudit'     : request.data['periods'][x]['financialStatementAudit'],
                'managementReport'            : request.data['periods'][x]['managementReport'],
                'certificateOfStockOwnership' : request.data['periods'][x]['certificateOfStockOwnership'],
                'rentDeclaration'             : request.data['periods'][x]['rentDeclaration'],
                'periodStartDate'             : request.data['periods'][x]['periodStartDate'] if request.data['periods'][x]['periodStartDate'] else None,
                'periodEndDate'               : request.data['periods'][x]['periodEndDate'] if request.data['periods'][x]['periodEndDate'] else None,
                'periodDays'                  : request.data['periods'][x]['periodDays'] if request.data['periods'][x]['periodDays'] else None,
                'assets'                      : assets.data['id'],
                'periodRange'                 : request.data['periods'][x]['periodRange'] if request.data['periods'][x]['periodRange'] else None,
                'passives'                    : passives.data['id'],
                'patrimony'                   : patrimony.data['id'],
                'stateOfResult'               : stateOfResult.data['id'],
                })
            # save financial profile
            serializer = FinancialProfileSerializer(data=financialProfiles, many=True, context={'request': request})
            
            if serializer.is_valid():
                serializer.save()
                # create the overviews of the client
                if 'analisis' in request.data:
                    client = Client.objects.get(pk=request.data['periods'][0]['client'])
                    Overview.objects.create(id=gen_uuid() ,client=client, qualitativeOverview=request.data['analisis']['qualitativeOverview'], financialAnalisis=request.data['analisis']['financialAnalisis'])
                # create the financial central
                if 'financialCentrals' in request.data:
                    for x in request.data['financialCentrals']:
                        FinancialCentral.objects.create(id=gen_uuid(), client=client, bank=Bank.objects.get(pk=x['bank']), centralBalances=x['centralBalances'], rating=x['rating'])
                return response({'error': False, 'data': {
                    'financialProfiles': serializer.data,
                    'overview': request.data['analisis'] if 'analisis' in request.data else None,
                    'financialCentrals': request.data['financialCentrals'] if 'financialCentrals' in request.data else None
                }}, 201)
            return response({'error': True, 'message': serializer.errors}, 400)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)

    @checkRole(['admin'])
    def get(self, request, pk=None, periods=3):
        try:
            if pk:
                logger.debug(f"'pk 1': {pk }")
        
                financialProfile = FinancialProfile.objects.filter(client=pk).order_by('-period')[:periods]
                logger.debug(f"financialProfile': {financialProfile }")
                logger.debug(f"'pk 2': {pk }")
                serializer       = FinancialProfileReadOnlySerializer(financialProfile,many=True)
                logger.debug(f"serializer : {serializer}")
                logger.debug(f"'pk 3': {pk }")
                # Get the analysis of the client
                overview = Overview.objects.filter(client=pk)
                logger.debug(f"'pk 4': {pk }")
                serializerOverview = OverviewSerializer(overview, many=True)
                logger.debug(f"'pk 5': {pk }")
                # Get the financial centrals of the client
                financialCentrals = FinancialCentral.objects.filter(client=pk)
                logger.debug(f"'pk 6': {pk }")
                serializerFinancialCentrals = FinancialCentralReadOnlySerializer(financialCentrals, many=True)
                logger.debug(serializer.data)
                logger.debug(f"serializerOverview.data {serializerOverview.data}")
                logger.debug(serializerFinancialCentrals.data )
                logger.debug({
                    'financialProfiles': serializer.data if len(serializer.data) > 0 else [],
                    'overview': serializerOverview.data[0] if len(serializerOverview.data) > 0 else [],
                    'financialCentrals': serializerFinancialCentrals.data if len(serializerFinancialCentrals.data) > 0 else []
                })
                return response({'error': False, 'data': {
                    'financialProfiles': serializer.data if len(serializer.data) > 0 else [],
                    'overview': serializerOverview.data[0] if len(serializerOverview.data) > 0 else [],
                    'financialCentrals': serializerFinancialCentrals.data if len(serializerFinancialCentrals.data) > 0 else []
                }}, 200)
            
            logger.debug(f"'pk 7': {pk }")
            financialProfiles = FinancialProfile.objects.all()
            logger.debug(f"'pk 8': {pk }")
            serializer = FinancialProfileSerializer(financialProfiles, many=True)
            logger.debug(f"'pk 9: {pk }")
            return response({'error': False, 'data': serializer.data}, 200)
        except FinancialProfile.DoesNotExist:
            return response({'error': True, 'message': 'Perfil financiero no encontrado'}, 404)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
    
    @checkRole(['admin'])
    def patch(self, request, pk=None):
        try:
            if request.data['clientId'] != None:
                client = Client.objects.get(pk=request.data['clientId'])
                if 'analisis' in request.data:
                # validate if the client has an overview
                    if Overview.objects.filter(client=client).exists():
                        overview = Overview.objects.get(client=client)
                        if 'qualitativeOverview' in request.data['analisis']:
                            overview.qualitativeOverview = request.data['analisis']['qualitativeOverview']
                        if 'financialAnalisis' in request.data['analisis']:
                            overview.financialAnalisis   = request.data['analisis']['financialAnalisis']
                        overview.save()
                    else:
                        Overview.objects.create(id=gen_uuid() ,client=client, qualitativeOverview=request.data['analisis']['qualitativeOverview'], financialAnalisis=request.data['analisis']['financialAnalisis'])
                    # validate if financialCentrals is in the request
                if 'financialCentrals' in request.data:
                    # validate if the client has financial centrals
                    if FinancialCentral.objects.filter(client=client).exists():
                        financialCentrals = FinancialCentral.objects.filter(client=client)
                        for x in financialCentrals:
                            x.delete()
                        # create the financial central
                    for x in request.data['financialCentrals']:
                        FinancialCentral.objects.create(id=gen_uuid(), client=client, bank=Bank.objects.get(pk=x['bank']), centralBalances=x['centralBalances'], rating=x['rating'])

                return response({'error': False, 'data': {
                            'analisis': request.data['analisis'] if 'analisis' in request.data else None,
                            'financialCentrals': request.data['financialCentrals'] if 'financialCentrals' in request.data else None
                        }}, 200)
            else:
                financialProfile = FinancialProfile.objects.get(pk=pk)
                serializer       = FinancialProfileUpdateSerializer(financialProfile, data=request.data, partial=True, context={'request': request})
                if serializer.is_valid():
                    serializer.save()
                else:
                    return response({'error': True, 'message': serializer.errors}, 400)              
                return response({'error': False, 'data': serializer.data}, 200)
        except FinancialProfile.DoesNotExist:
            return response({'error': True, 'message': 'Perfil financiero no encontrado'}, 404)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)


# Client Indicators
class FinancialProfileIndicatorsAV(APIView):

    @checkRole(['admin'])
    def get(self, request, pk):
        try:
            indicators = calcReportVariability("","", pk)
            logger.debug(f"'indicators': {indicators}")
            # get client data
            if len(request.query_params) > 0:
                client = Client.objects.get(pk=pk)
                data = {
                    'client'    : client.social_reason if client.social_reason != None else client.first_name + ' ' + client.last_name,
                    'document'  : client.document_number,
                    'activity'  : client.ciiu.activity.description if client.ciiu else '',
                    'indicators': indicators
                }
                template      = get_template('financialStatement.html')
                logger.debug(f"'parseTemplate':{ data}")
                parseTemplate = template.render(data)
                logger.debug(f"'parseTemplate':{ parseTemplate}")
                parsePdf      = pdfToBase64(parseTemplate)
                return response({'error': False, 'data': parsePdf['pdf']}, 200)
            return response({'error': False, 'data': indicators}, 200)
        except Exception as e:
            return response({'error': True, 'data':str(e)}, 500)
