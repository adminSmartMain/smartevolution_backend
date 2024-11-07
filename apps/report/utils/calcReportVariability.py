from apps.client.api.serializers.index import FinancialProfilePeriodSerializer, FinancialProfilePeriodSerializer

# Models
from apps.client.models import FinancialProfile
# Utils 
from apps.client.utils.index import calcActivityEfficiency, calcFinancialRisk, calcRentability, calcResults, calcVariability
from apps.base.exceptions import HttpException



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

def calcReportVariability(emitter, payer, client=None):
    try: 
            # indicators object
            indicators = {
                'activityEfficiency': {
                    'period_1' : {},
                    'period_2' : {},
                    'period_3' : {}
                },
                'rentability': {
                    'period_1': {},
                    'period_2': {},
                    'period_3': {}
                },
                'financialRisk':{
                    'period_1': {},
                    'period_2': {},
                    'period_3': {}
                },
                'results': {
                    'period_1': {},
                    'period_2': {},
                    'period_3': {}
                },
                'variability': {
                    'period_2':{},
                    'period_3':{}
                }

            }
            if client:
                financialProfile = FinancialProfile.objects.filter(client=client).order_by('-period')[:3]
                serializer       = FinancialProfilePeriodSerializer(financialProfile, many=True)
                # check the number of periods
                length = len(serializer.data)
                if length == 1:

                    match(serializer.data[0]['typePeriod']):
                        case 'a12eec8b-06e1-4fbc-a888-d33364032151':
                            periodDays = serializer.data[0]['periodDays']
                        case '0835dcb5-d6f2-43d7-b7ca-8864119ea05f':
                            periodDays = 360
                        case 'e635f0f1-b29c-45e5-b351-04725a489be3':
                            periodDays = 180
                        case 'e7b663d7-5cc3-4a9f-b288-95ce38c1ccfd':
                            periodDays = 90

                    period_1 = {
                        'period'       : serializer.data[0]['period'],
                        'typePeriod'   : serializer.data[0]['typePeriod'],
                        'periodDays'   : periodDays,
                        'assets'       : serializer.data[0]['assets'],
                        'passives'     : serializer.data[0]['passives'],
                        'patrimony'    : serializer.data[0]['patrimony'],
                        'stateOfResult': serializer.data[0]['stateOfResult']
                    }
                    for index, period in enumerate([period_1]):
                        # Calc activity efficiency
                        logger.debug(f"calcActivityEfficiency: {calcActivityEfficiency(indicators, index, period)}")
                        indicators.update(calcActivityEfficiency(indicators, index, period))
                        # Calc rentability
                        indicators.update(calcRentability(indicators, index, period))
                        # calc financial risk
                        indicators.update(calcFinancialRisk(indicators, index, period))
                        # calc results
                        indicators.update(calcResults(indicators, index, period))

                    # Calc variability
                    indicators.update(calcVariability(indicators, period_1))
                    logger.debug(f"calcVariability: {calcVariability(indicators, period_1)}")

                elif length == 2:
                    match(serializer.data[1]['typePeriod']):
                        case 'a12eec8b-06e1-4fbc-a888-d33364032151':
                            periodDays = serializer.data[1]['periodDays']
                        case '0835dcb5-d6f2-43d7-b7ca-8864119ea05f':
                            periodDays = 360
                        case 'e635f0f1-b29c-45e5-b351-04725a489be3':
                            periodDays = 180
                        case 'e7b663d7-5cc3-4a9f-b288-95ce38c1ccfd':
                            periodDays = 90

                    period_1 = {
                        'period'       : serializer.data[1]['period'],
                        'typePeriod'   : serializer.data[1]['typePeriod'],
                        'periodDays'   : periodDays,
                        'assets'       : serializer.data[1]['assets'],
                        'passives'     : serializer.data[1]['passives'],
                        'patrimony'    : serializer.data[1]['patrimony'],
                        'stateOfResult': serializer.data[1]['stateOfResult']
                    }

                    match(serializer.data[0]['typePeriod']):
                        case 'a12eec8b-06e1-4fbc-a888-d33364032151':
                            periodDays2 = serializer.data[0]['periodDays']
                        case '0835dcb5-d6f2-43d7-b7ca-8864119ea05f':
                            periodDays2 = 360
                        case 'e635f0f1-b29c-45e5-b351-04725a489be3':
                            periodDays2 = 180
                        case 'e7b663d7-5cc3-4a9f-b288-95ce38c1ccfd':
                            periodDays2 = 90
                    period_2 = {
                        'period'       : serializer.data[0]['period'],
                        'typePeriod'   : serializer.data[0]['typePeriod'],
                        'periodDays'   : periodDays2,
                        'assets'       : serializer.data[0]['assets'],
                        'passives'     : serializer.data[0]['passives'],
                        'patrimony'    : serializer.data[0]['patrimony'],
                        'stateOfResult': serializer.data[0]['stateOfResult']
                    }
                    for index, period in enumerate([period_1, period_2]):
                        # Calc activity efficiency
                        indicators.update(calcActivityEfficiency(indicators, index, period))
                        # Calc rentability
                        indicators.update(calcRentability(indicators, index, period))
                        # calc financial risk
                        indicators.update(calcFinancialRisk(indicators, index, period))
                        # calc results
                        indicators.update(calcResults(indicators, index, period))

                        # Calc variability
                        indicators.update(calcVariability(indicators, period_1, period_2))
                elif length == 3:
                    logger.debug(f"serializer.data[0]['stateOfResult']: {serializer.data[0]['stateOfResult']}")
                    match(serializer.data[2]['typePeriod']):
                        case 'a12eec8b-06e1-4fbc-a888-d33364032151':
                            periodDays = serializer.data[0]['periodDays']
                        case '0835dcb5-d6f2-43d7-b7ca-8864119ea05f':
                            periodDays = 360
                        case 'e635f0f1-b29c-45e5-b351-04725a489be3':
                            periodDays = 180
                        case 'e7b663d7-5cc3-4a9f-b288-95ce38c1ccfd':
                            periodDays = 90
                    period_1 = {
                        'period'       : serializer.data[2]['period'],
                        'typePeriod'   : serializer.data[2]['typePeriod'],
                        'periodDays'   : periodDays,
                        'assets'       : serializer.data[2]['assets'],
                        'passives'     : serializer.data[2]['passives'],
                        'patrimony'    : serializer.data[2]['patrimony'],
                        'stateOfResult': serializer.data[2]['stateOfResult']
                    }
                    match(serializer.data[1]['typePeriod']):
                        case 'a12eec8b-06e1-4fbc-a888-d33364032151':
                            periodDays2 = serializer.data[1]['periodDays']
                        case '0835dcb5-d6f2-43d7-b7ca-8864119ea05f':
                            periodDays2 = 360
                        case 'e635f0f1-b29c-45e5-b351-04725a489be3':
                            periodDays2 = 180
                        case 'e7b663d7-5cc3-4a9f-b288-95ce38c1ccfd':
                            periodDays2 = 90
                    period_2 = {
                        'period'       : serializer.data[1]['period'],
                        'typePeriod'   : serializer.data[1]['typePeriod'],
                        'periodDays'   : periodDays2,
                        'assets'       : serializer.data[1]['assets'],
                        'passives'     : serializer.data[1]['passives'],
                        'patrimony'    : serializer.data[1]['patrimony'],
                        'stateOfResult': serializer.data[1]['stateOfResult']
                    }
                    match(serializer.data[0]['typePeriod']):
                        case 'a12eec8b-06e1-4fbc-a888-d33364032151':
                            periodDays3 = serializer.data[0]['periodDays']
                        case '0835dcb5-d6f2-43d7-b7ca-8864119ea05f':
                            periodDays3 = 360
                        case 'e635f0f1-b29c-45e5-b351-04725a489be3':
                            periodDays3 = 180
                        case 'e7b663d7-5cc3-4a9f-b288-95ce38c1ccfd':
                            periodDays3 = 90
                    period_3 = {
                        'period'       : serializer.data[0]['period'],
                        'typePeriod'   : serializer.data[0]['typePeriod'],
                        'periodDays'   : periodDays3,
                        'assets'       : serializer.data[0]['assets'],
                        'passives'     : serializer.data[0]['passives'],
                        'patrimony'    : serializer.data[0]['patrimony'],
                        'stateOfResult': serializer.data[0]['stateOfResult']
                    }
                    for index, period in enumerate([period_1, period_2, period_3]):
                        # Calc activity efficiency
                        indicators.update(calcActivityEfficiency(indicators, index, period))
                        logger.debug(f"calcActivityEfficiency: {calcActivityEfficiency(indicators, index, period)}")
                        logger.debug(f"serializer.data[2]['stateOfResult']: {serializer.data[2]['stateOfResult']}")
                        # Calc rentability
                        indicators.update(calcRentability(indicators, index, period))
                        # calc financial risk
                        indicators.update(calcFinancialRisk(indicators, index, period))
                        # calc results
                        indicators.update(calcResults(indicators, index, period))

                        # Calc variability
                        indicators.update(calcVariability(indicators, period_1, period_2, period_3))
                        logger.debug(f"calcVariability: {calcVariability(indicators, period_1, period_2, period_3)}")
            else:
                dataReport = {
                    'emitter': {},
                    'payer': {}
                }

                # calc emitter
                if emitter != "":
                    logger.debug(f"entramos a emitter")
                    financialProfile = FinancialProfile.objects.filter(client=emitter).order_by('-period')[:3]
                    serializer       = FinancialProfilePeriodSerializer(financialProfile, many=True)
                    # check the number of periods
                    length = len(serializer.data)
                    if length == 0:
                        logger.debug(f"llenamos emitter de dataReport")
                        dataReport['emitter']= indicators
                    if length == 1:
                        logger.debug(f"emisor length == 1")
                        try:
                            logger.debug(f"serializer.data {serializer.data}")
                            logger.debug(f"primer periodo {serializer.data[0]}")
                            logger.debug(f"caso un periodo")
                            
                            match(serializer.data[0]['typePeriod']):
                                case 'a12eec8b-06e1-4fbc-a888-d33364032151':
                                    periodDays = serializer.data[0]['periodDays']
                                case '0835dcb5-d6f2-43d7-b7ca-8864119ea05f':
                                    periodDays = 360
                                case 'e635f0f1-b29c-45e5-b351-04725a489be3':
                                    periodDays = 180
                                case 'e7b663d7-5cc3-4a9f-b288-95ce38c1ccfd':
                                    periodDays = 90
                            logger.debug(f"creacion periodo 1")
                            period_1 = {
                                'period'       : serializer.data[0]['period'],
                                'typePeriod'   : serializer.data[0]['typePeriod'],
                                'periodDays'   : periodDays,
                                'assets'       : serializer.data[0]['assets'],
                                'passives'     : serializer.data[0]['passives'],
                                'patrimony'    : serializer.data[0]['patrimony'],
                                'stateOfResult': serializer.data[0]['stateOfResult']
                            }
                            logger.debug(f"periodo 1 creado")
                            logger.debug(f"está entrando al try antes de calcular acrividad eficiencia")
                            for index, period in enumerate([period_1]):
                                logger.debug(f"Calc activity efficiency")
                                # Calc activity efficiency
                                indicators.update(calcActivityEfficiency(indicators, index, period))
                                logger.debug(f"calculado activity efficiency")
                                # Calc rentability
                                indicators.update(calcRentability(indicators, index, period))
                                logger.debug(f"calculado Rentability")
                                # calc financial risk
                                indicators.update(calcFinancialRisk(indicators, index, period))
                                logger.debug(f"calculado FinancialRIsk")
                                # calc results
                                indicators.update(calcResults(indicators, index, period))
                                logger.debug(f"calculado calcResults")
                                logger.debug(f"index + 1 {index + 1}")
                                dataReport['emitter'][f'period_{index + 1}'] = period
                                dataReport['emitter'][f'period_{index + 1}']['activityEfficiency'] = indicators['activityEfficiency'][f'period_{index + 1}']
                                dataReport['emitter'][f'period_{index + 1}']['rentability'] = indicators['rentability'][f'period_{index + 1}']
                                dataReport['emitter'][f'period_{index + 1}']['financialRisk'] = indicators['financialRisk'][f'period_{index + 1}']
                                dataReport['emitter'][f'period_{index + 1}']['results'] = indicators['results'][f'period_{index + 1}']    
                                # Calc variability
                            logger.debug(f"calculando calcVariability")
                            indicators.update(calcVariability(indicators, period_1))
                            logger.debug(f"calculado calcVariability")
                            logger.debug(f"calculado calcVariability {indicators['variability']}")
                            
                            
                            dataReport['emitter']['variability'] = indicators['variability']
                           
                        except Exception as e:
                            logger.error(f"Unexpected error: {e}")
                    elif length == 2:
                        logger.debug(f"caso dos periodo")
                        match(serializer.data[1]['typePeriod']):
                            case 'a12eec8b-06e1-4fbc-a888-d33364032151':
                                periodDays = serializer.data[1]['periodDays']
                            case '0835dcb5-d6f2-43d7-b7ca-8864119ea05f':
                                periodDays = 360
                            case 'e635f0f1-b29c-45e5-b351-04725a489be3':
                                periodDays = 180
                            case 'e7b663d7-5cc3-4a9f-b288-95ce38c1ccfd':
                                periodDays = 90
                        period_1 = {
                            'period'       : serializer.data[1]['period'],
                            'typePeriod'   : serializer.data[1]['typePeriod'],
                            'periodDays'   : periodDays,
                            'assets'       : serializer.data[1]['assets'],
                            'passives'     : serializer.data[1]['passives'],
                            'patrimony'    : serializer.data[1]['patrimony'],
                            'stateOfResult': serializer.data[1]['stateOfResult']
                        }

                        match(serializer.data[0]['typePeriod']):
                            case 'a12eec8b-06e1-4fbc-a888-d33364032151':
                                periodDays2 = serializer.data[0]['periodDays']
                            case '0835dcb5-d6f2-43d7-b7ca-8864119ea05f':
                                periodDays2 = 360
                            case 'e635f0f1-b29c-45e5-b351-04725a489be3':
                                periodDays2 = 180
                            case 'e7b663d7-5cc3-4a9f-b288-95ce38c1ccfd':
                                periodDays2 = 90
                        period_2 = {
                            'period'       : serializer.data[0]['period'],
                            'typePeriod'   : serializer.data[0]['typePeriod'],
                            'periodDays'   : periodDays2,
                            'assets'       : serializer.data[0]['assets'],
                            'passives'     : serializer.data[0]['passives'],
                            'patrimony'    : serializer.data[0]['patrimony'],
                            'stateOfResult': serializer.data[0]['stateOfResult']
                        }
                        for index, period in enumerate([period_1, period_2]):
                            logger.debug(f"serializer : {serializer}")
                            logger.debug(f"serializer periodo 3: {serializer.data[1]['stateOfResult']}")
                            # Calc activity efficiency
                            indicators.update(calcActivityEfficiency(indicators, index, period))
                            # Calc rentability
                            indicators.update(calcRentability(indicators, index, period))
                            # calc financial risk
                            indicators.update(calcFinancialRisk(indicators, index, period))
                            # calc results
                            indicators.update(calcResults(indicators, index, period))
                            dataReport['emitter'][f'period_{index + 1}'] = period
                            dataReport['emitter'][f'period_{index + 1}']['activityEfficiency'] = indicators['activityEfficiency'][f'period_{index + 1}']
                            dataReport['emitter'][f'period_{index + 1}']['rentability'] = indicators['rentability'][f'period_{index + 1}']
                            dataReport['emitter'][f'period_{index + 1}']['financialRisk'] = indicators['financialRisk'][f'period_{index + 1}']
                            dataReport['emitter'][f'period_{index + 1}']['results'] = indicators['results'][f'period_{index + 1}']    
                        # Calc variability
                        indicators.update(calcVariability(indicators, period_1, period_2))
                        dataReport['emitter']['variability'] = indicators['variability']
                            # Calc variability
                    elif length == 3:
                        logger.debug(f"caso tres periodo")
                        match(serializer.data[2]['typePeriod']):
                            case 'a12eec8b-06e1-4fbc-a888-d33364032151':
                                periodDays = serializer.data[2]['periodDays']
                            case '0835dcb5-d6f2-43d7-b7ca-8864119ea05f':
                                periodDays = 360
                            case 'e635f0f1-b29c-45e5-b351-04725a489be3':
                                periodDays = 180
                            case 'e7b663d7-5cc3-4a9f-b288-95ce38c1ccfd':
                                periodDays = 90
                        period_1 = {
                            'period'       : serializer.data[2]['period'],
                            'typePeriod'   : serializer.data[2]['typePeriod'],
                            'periodDays'   : periodDays,
                            'assets'       : serializer.data[2]['assets'],
                            'passives'     : serializer.data[2]['passives'],
                            'patrimony'    : serializer.data[2]['patrimony'],
                            'stateOfResult': serializer.data[2]['stateOfResult']
                        }
                        match(serializer.data[1]['typePeriod']):
                            case 'a12eec8b-06e1-4fbc-a888-d33364032151':
                                periodDays2 = serializer.data[1]['periodDays']
                            case '0835dcb5-d6f2-43d7-b7ca-8864119ea05f':
                                periodDays2 = 360
                            case 'e635f0f1-b29c-45e5-b351-04725a489be3':
                                periodDays2 = 180
                            case 'e7b663d7-5cc3-4a9f-b288-95ce38c1ccfd':
                                periodDays2 = 90
                        period_2 = {
                            'period'       : serializer.data[1]['period'],
                            'typePeriod'   : serializer.data[1]['typePeriod'],
                            'periodDays'   : periodDays2,
                            'assets'       : serializer.data[1]['assets'],
                            'passives'     : serializer.data[1]['passives'],
                            'patrimony'    : serializer.data[1]['patrimony'],
                            'stateOfResult': serializer.data[1]['stateOfResult']
                        }
                        match(serializer.data[0]['typePeriod']):
                            case 'a12eec8b-06e1-4fbc-a888-d33364032151':
                                periodDays3 = serializer.data[0]['periodDays']
                            case '0835dcb5-d6f2-43d7-b7ca-8864119ea05f':
                                periodDays3 = 360
                            case 'e635f0f1-b29c-45e5-b351-04725a489be3':
                                periodDays3 = 180
                            case 'e7b663d7-5cc3-4a9f-b288-95ce38c1ccfd':
                                periodDays3 = 90
                        period_3 = {
                            'period'       : serializer.data[0]['period'],
                            'typePeriod'   : serializer.data[0]['typePeriod'],
                            'periodDays'   : periodDays3,
                            'assets'       : serializer.data[0]['assets'],
                            'passives'     : serializer.data[0]['passives'],
                            'patrimony'    : serializer.data[0]['patrimony'],
                            'stateOfResult': serializer.data[0]['stateOfResult']
                        }
                        for index, period in enumerate([period_1, period_2, period_3]):
                            # Calc activity efficiency
                            indicators.update(calcActivityEfficiency(indicators, index, period))
                            logger.debug(f"serializer: {serializer.data}")
                            logger.debug(f"serializer periodo 3: {serializer.data[2]['stateOfResult']}")
                            logger.debug(f"serializer periodo 2: {serializer.data[1]['stateOfResult']}")
                            logger.debug(f"serializer periodo 1: {serializer.data[0]['stateOfResult']}")
                            logger.debug(f"calcActivityEfficiency: {calcActivityEfficiency(indicators, index, period)}")
                            # Calc rentability
                            indicators.update(calcRentability(indicators, index, period))
                            # calc financial risk
                            indicators.update(calcFinancialRisk(indicators, index, period))
                            # calc results
                            indicators.update(calcResults(indicators, index, period))
                            dataReport['emitter'][f'period_{index + 1}'] = period
                            dataReport['emitter'][f'period_{index + 1}']['activityEfficiency'] = indicators['activityEfficiency'][f'period_{index + 1}']
                            dataReport['emitter'][f'period_{index + 1}']['rentability'] = indicators['rentability'][f'period_{index + 1}']
                            dataReport['emitter'][f'period_{index + 1}']['financialRisk'] = indicators['financialRisk'][f'period_{index + 1}']
                            dataReport['emitter'][f'period_{index + 1}']['results'] = indicators['results'][f'period_{index + 1}']    
                        # Calc variability
                        indicators.update(calcVariability(indicators, period_1, period_2, period_3))
                        logger.debug(f"calcActivityEfficiency: {calcVariability(indicators, period_1, period_2, period_3)}")
                        dataReport['emitter']['variability'] = indicators['variability']
                        
                        logger.debug(f"variability: {dataReport['emitter']['variability']}")
                # calc payer/s indicators
                if payer != "":
                    logger.debug(f"entramos a pagadores")
                    financialProfile = FinancialProfile.objects.filter(client=payer).order_by('-period')[:3]
                    serializer       = FinancialProfilePeriodSerializer(financialProfile, many=True)
                    # check the number of periods
                    length = len(serializer.data)
                    if length == 0:
                        dataReport['payer'] = indicators

                    elif length == 1:
                        logger.debug(f"caso lenght ==1 en pagador")
                        try:
                            match(serializer.data[0]['typePeriod']):
                                case 'a12eec8b-06e1-4fbc-a888-d33364032151':
                                    periodDays = serializer.data[0]['periodDays']
                                case '0835dcb5-d6f2-43d7-b7ca-8864119ea05f':
                                    periodDays = 360
                                case 'e635f0f1-b29c-45e5-b351-04725a489be3':
                                    periodDays = 180
                                case 'e7b663d7-5cc3-4a9f-b288-95ce38c1ccfd':
                                    periodDays = 90

                            period_1 = {
                                'period'       : serializer.data[0]['period'],
                                'typePeriod'   : serializer.data[0]['typePeriod'],
                                'periodDays'   : periodDays,
                                'assets'       : serializer.data[0]['assets'],
                                'passives'     : serializer.data[0]['passives'],
                                'patrimony'    : serializer.data[0]['patrimony'],
                                'stateOfResult': serializer.data[0]['stateOfResult']
                            }
                            for index, period in enumerate([period_1]):
                                # Calc activity efficiency
                                indicators.update(calcActivityEfficiency(indicators, index, period))
                                # Calc rentability
                                indicators.update(calcRentability(indicators, index, period))
                                # calc financial risk
                                indicators.update(calcFinancialRisk(indicators, index, period))
                                # calc results
                                indicators.update(calcResults(indicators, index, period))
                                dataReport['payer'][f'period_{index + 1}'] = period
                                dataReport['payer'][f'period_{index + 1}']['activityEfficiency'] = indicators['activityEfficiency'][f'period_{index + 1}']
                                dataReport['payer'][f'period_{index + 1}']['rentability'] = indicators['rentability'][f'period_{index + 1}']
                                dataReport['payer'][f'period_{index + 1}']['financialRisk'] = indicators['financialRisk'][f'period_{index + 1}']
                                dataReport['payer'][f'period_{index + 1}']['results'] = indicators['results'][f'period_{index + 1}']    
                            # Calc variability
                            indicators.update(calcVariability(indicators, period_1))
                            dataReport['payer']['variability'] = indicators['variability']
                        except Exception as e:
                            logger.error(f"Unexpected error: {e}")
                            

                    elif length == 2:
                        logger.debug(f"caso lenght ==3 en pagador")
                        match(serializer.data[1]['typePeriod']):
                            case 'a12eec8b-06e1-4fbc-a888-d33364032151':
                                periodDays = serializer.data[1]['periodDays']
                            case '0835dcb5-d6f2-43d7-b7ca-8864119ea05f':
                                periodDays = 360
                            case 'e635f0f1-b29c-45e5-b351-04725a489be3':
                                periodDays = 180
                            case 'e7b663d7-5cc3-4a9f-b288-95ce38c1ccfd':
                                periodDays = 90
                        period_1 = {
                            'period'       : serializer.data[1]['period'],
                            'typePeriod'   : serializer.data[1]['typePeriod'],
                            'periodDays'   : periodDays,
                            'assets'       : serializer.data[1]['assets'],
                            'passives'     : serializer.data[1]['passives'],
                            'patrimony'    : serializer.data[1]['patrimony'],
                            'stateOfResult': serializer.data[1]['stateOfResult']
                        }

                        match(serializer.data[0]['typePeriod']):
                            case 'a12eec8b-06e1-4fbc-a888-d33364032151':
                                periodDays2 = serializer.data[0]['periodDays']
                            case '0835dcb5-d6f2-43d7-b7ca-8864119ea05f':
                                periodDays2 = 360
                            case 'e635f0f1-b29c-45e5-b351-04725a489be3':
                                periodDays2 = 180
                            case 'e7b663d7-5cc3-4a9f-b288-95ce38c1ccfd':
                                periodDays2 = 90
                        period_2 = {
                            'period'       : serializer.data[0]['period'],
                            'typePeriod'   : serializer.data[0]['typePeriod'],
                            'periodDays'   : periodDays2,
                            'assets'       : serializer.data[0]['assets'],
                            'passives'     : serializer.data[0]['passives'],
                            'patrimony'    : serializer.data[0]['patrimony'],
                            'stateOfResult': serializer.data[0]['stateOfResult']
                        }
                        for index, period in enumerate([period_1, period_2]):
                            # Calc activity efficiency
                            indicators.update(calcActivityEfficiency(indicators, index, period))
                            # Calc rentability
                            indicators.update(calcRentability(indicators, index, period))
                            # calc financial risk
                            indicators.update(calcFinancialRisk(indicators, index, period))
                            # calc results
                            indicators.update(calcResults(indicators, index, period))
                            dataReport['payer'][f'period_{index + 1}'] = period
                            dataReport['payer'][f'period_{index + 1}']['activityEfficiency'] = indicators['activityEfficiency'][f'period_{index + 1}']
                            dataReport['payer'][f'period_{index + 1}']['rentability'] = indicators['rentability'][f'period_{index + 1}']
                            dataReport['payer'][f'period_{index + 1}']['financialRisk'] = indicators['financialRisk'][f'period_{index + 1}']
                            dataReport['payer'][f'period_{index + 1}']['results'] = indicators['results'][f'period_{index + 1}']    
                        # Calc variability
                        indicators.update(calcVariability(indicators, period_1, period_2))
                        dataReport['payer']['variability'] = indicators['variability']
                    elif length == 3:
                        logger.debug(f"caso lenght ==3 en pagador")
                        match(serializer.data[2]['typePeriod']):
                            case 'a12eec8b-06e1-4fbc-a888-d33364032151':
                                periodDays = serializer.data[2]['periodDays']
                            case '0835dcb5-d6f2-43d7-b7ca-8864119ea05f':
                                periodDays = 360
                            case 'e635f0f1-b29c-45e5-b351-04725a489be3':
                                periodDays = 180
                            case 'e7b663d7-5cc3-4a9f-b288-95ce38c1ccfd':
                                periodDays = 90
                        period_1 = {
                            'period'       : serializer.data[2]['period'],
                            'typePeriod'   : serializer.data[2]['typePeriod'],
                            'periodDays'   : periodDays,
                            'assets'       : serializer.data[2]['assets'],
                            'passives'     : serializer.data[2]['passives'],
                            'patrimony'    : serializer.data[2]['patrimony'],
                            'stateOfResult': serializer.data[2]['stateOfResult']
                        }
                        match(serializer.data[1]['typePeriod']):
                            case 'a12eec8b-06e1-4fbc-a888-d33364032151':
                                periodDays2 = serializer.data[1]['periodDays']
                            case '0835dcb5-d6f2-43d7-b7ca-8864119ea05f':
                                periodDays2 = 360
                            case 'e635f0f1-b29c-45e5-b351-04725a489be3':
                                periodDays2 = 180
                            case 'e7b663d7-5cc3-4a9f-b288-95ce38c1ccfd':
                                periodDays2 = 90
                        period_2 = {
                            'period'       : serializer.data[1]['period'],
                            'typePeriod'   : serializer.data[1]['typePeriod'],
                            'periodDays'   : periodDays2,
                            'assets'       : serializer.data[1]['assets'],
                            'passives'     : serializer.data[1]['passives'],
                            'patrimony'    : serializer.data[1]['patrimony'],
                            'stateOfResult': serializer.data[1]['stateOfResult']
                        }
                        match(serializer.data[0]['typePeriod']):
                            case 'a12eec8b-06e1-4fbc-a888-d33364032151':
                                periodDays3 = serializer.data[0]['periodDays']
                            case '0835dcb5-d6f2-43d7-b7ca-8864119ea05f':
                                periodDays3 = 360
                            case 'e635f0f1-b29c-45e5-b351-04725a489be3':
                                periodDays3 = 180
                            case 'e7b663d7-5cc3-4a9f-b288-95ce38c1ccfd':
                                periodDays3 = 90
                        period_3 = {
                            'period'       : serializer.data[0]['period'],
                            'typePeriod'   : serializer.data[0]['typePeriod'],
                            'periodDays'   : periodDays3,
                            'assets'       : serializer.data[0]['assets'],
                            'passives'     : serializer.data[0]['passives'],
                            'patrimony'    : serializer.data[0]['patrimony'],
                            'stateOfResult': serializer.data[0]['stateOfResult']
                        }
                        for index, period in enumerate([period_1, period_2, period_3]):
                            # Calc activity efficiency
                            indicators.update(calcActivityEfficiency(indicators, index, period))
                            # Calc rentability
                            indicators.update(calcRentability(indicators, index, period))
                            # calc financial risk
                            indicators.update(calcFinancialRisk(indicators, index, period))
                            # calc results
                            indicators.update(calcResults(indicators, index, period))
                            dataReport['payer'][f'period_{index + 1}'] = period
                            dataReport['payer'][f'period_{index + 1}']['activityEfficiency'] = indicators['activityEfficiency'][f'period_{index + 1}']
                            dataReport['payer'][f'period_{index + 1}']['rentability'] = indicators['rentability'][f'period_{index + 1}']
                            dataReport['payer'][f'period_{index + 1}']['financialRisk'] = indicators['financialRisk'][f'period_{index + 1}']
                            dataReport['payer'][f'period_{index + 1}']['results'] = indicators['results'][f'period_{index + 1}']    
                        # Calc variability
                        indicators.update(calcVariability(indicators, period_1, period_2,period_3))
                        dataReport['payer']['variability'] = indicators['variability']
            return indicators if client else dataReport
    except Exception as e:
        raise e