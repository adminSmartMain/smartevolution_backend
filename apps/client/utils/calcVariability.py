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

def calcVariability(indicators, period1, period2=None, period3=None):
    #period 2 variability
    if period2 != None:
        #period
        indicators['variability']['period_2']['period'] = period2['period'] 
        
        #net sales
        indicators['variability']['period_2']['net_sales'] = float('{:.1f}'.format(((period2['stateOfResult']['net_sales'] - \
            period1['stateOfResult']['net_sales']) / (period1['stateOfResult']['net_sales'])) *100))
        
        
        #operating_profit
        indicators['variability']['period_2']['operating_profit'] = float('{:.1f}'.format(((period2['stateOfResult']['operating_profit'] -
            period1['stateOfResult']['operating_profit']) / (period1['stateOfResult']['operating_profit'])) * 100))
        logger.debug(f"'operating_profit period 2': {indicators['variability']['period_2']['operating_profit'] }")
        
        #net_income
        indicators['variability']['period_2']['net_income'] = float('{:.1f}'.format(((period2['stateOfResult']['net_income'] -
            period1['stateOfResult']['net_income']) / (period1['stateOfResult']['net_income'])) * 100))
        
        
        #total_assets
        indicators['variability']['period_2']['total_assets'] = float('{:.1f}'.format(((period2['assets']['total_assets'] -
            period1['assets']['total_assets']) / (period1['assets']['total_assets'])) * 100))
        
        #total_passives
        
        indicators['variability']['period_2']['total_passives'] = float('{:.1f}'.format(((period2['passives']['total_passives'] -
            period1['passives']['total_passives']) / (period1['passives']['total_passives'])) * 100))
        
        #total_patrimony
        
        try:
        
            indicators['variability']['period_2']['total_patrimony'] = float('{:.1f}'.format(((period2['patrimony']['total_patrimony'] -
                period1['patrimony']['total_patrimony']) / (period1['patrimony']['total_patrimony'])) * 100))
            logger.debug(f"'total_patrimony period 2': {indicators['variability']['period_2']['total_patrimony'] }")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
    if period3 != None:    
        #period 3 variability
        indicators['variability']['period_3']['period']    = period3['period']
        indicators['variability']['period_3']['net_sales'] = float('{:.1f}'.format(((period3['stateOfResult']['net_sales'] - \
            period2['stateOfResult']['net_sales']) / period2['stateOfResult']['net_sales']) * 100))

        indicators['variability']['period_3']['operating_profit'] = float('{:.1f}'.format(((period3['stateOfResult']['operating_profit'] -
            period2['stateOfResult']['operating_profit']) / period2['stateOfResult']['operating_profit']) * 100))
        logger.debug(f"'operating_profit period3': {indicators['variability']['period_3']['operating_profit']}")
        logger.debug(f"'operating_profit period3 stateofResult': {period3['stateOfResult']['operating_profit']}")
        logger.debug(f"'operating_profit period2 stateofResult': {period2['stateOfResult']['operating_profit']}")
        
        
        indicators['variability']['period_3']['net_income'] = float('{:.1f}'.format(((period3['stateOfResult']['net_income'] -
            period2['stateOfResult']['net_income']) / period2['stateOfResult']['net_income']) * 100))

        indicators['variability']['period_3']['total_assets'] = float('{:.1f}'.format(((period3['assets']['total_assets'] -
            period2['assets']['total_assets']) / period2['assets']['total_assets']) * 100))

        indicators['variability']['period_3']['total_passives'] = float('{:.1f}'.format(((period3['passives']['total_passives'] -
            period2['passives']['total_passives']) / period2['passives']['total_passives']) * 100))
        try:
            logger.debug(f"entrando al try tercer periodo")
            indicators['variability']['period_3']['total_patrimony'] = round(float('{:.1f}'.format(((period3['patrimony']['total_patrimony'] -
                period2['patrimony']['total_patrimony']) / period2['patrimony']['total_patrimony']) * 100)),2)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
    logger.debug(f"'indicators calcVariability': {indicators}")
    
    return indicators