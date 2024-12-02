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
    # Period 2 variability
    if period2 is not None:
        try:
            indicators['variability']['period_2']['period'] = period2['period']
            
            # Net sales
            indicators['variability']['period_2']['net_sales'] = float('{:.1f}'.format(
                ((period2['stateOfResult']['net_sales'] - period1['stateOfResult']['net_sales']) /
                 period1['stateOfResult']['net_sales']) * 100
            ))
        except (KeyError, ZeroDivisionError, TypeError) as e:
            logger.error(f"Error calculating net_sales period_2: {e}")
        
        try:
            # Operating profit
            indicators['variability']['period_2']['operating_profit'] = float('{:.1f}'.format(
                ((period2['stateOfResult']['operating_profit'] - period1['stateOfResult']['operating_profit']) /
                 period1['stateOfResult']['operating_profit']) * 100
            ))
        except (KeyError, ZeroDivisionError, TypeError) as e:
            logger.error(f"Error calculating operating_profit period_2: {e}")

        try:
            # Net income
            indicators['variability']['period_2']['net_income'] = float('{:.1f}'.format(
                ((period2['stateOfResult']['net_income'] - period1['stateOfResult']['net_income']) /
                 period1['stateOfResult']['net_income']) * 100
            ))
        except (KeyError, ZeroDivisionError, TypeError) as e:
            logger.error(f"Error calculating net_income period_2: {e}")

        try:
            # Total assets
            indicators['variability']['period_2']['total_assets'] = float('{:.1f}'.format(
                ((period2['assets']['total_assets'] - period1['assets']['total_assets']) /
                 period1['assets']['total_assets']) * 100
            ))
        except (KeyError, ZeroDivisionError, TypeError) as e:
            logger.error(f"Error calculating total_assets period_2: {e}")

        try:
            # Total passives
            indicators['variability']['period_2']['total_passives'] = float('{:.1f}'.format(
                ((period2['passives']['total_passives'] - period1['passives']['total_passives']) /
                 period1['passives']['total_passives']) * 100
            ))
        except (KeyError, ZeroDivisionError, TypeError) as e:
            logger.error(f"Error calculating total_passives period_2: {e}")

        try:
            # Total patrimony
            indicators['variability']['period_2']['total_patrimony'] = float('{:.1f}'.format(
                ((period2['patrimony']['total_patrimony'] - period1['patrimony']['total_patrimony']) /
                 period1['patrimony']['total_patrimony']) * 100
            ))
        except (KeyError, ZeroDivisionError, TypeError) as e:
            logger.error(f"Error calculating total_patrimony period_2: {e}")

    # Period 3 variability
    if period3 is not None:
        try:
            indicators['variability']['period_3']['period'] = period3['period']

            # Net sales
            indicators['variability']['period_3']['net_sales'] = float('{:.1f}'.format(
                ((period3['stateOfResult']['net_sales'] - period2['stateOfResult']['net_sales']) /
                 period2['stateOfResult']['net_sales']) * 100
            ))
        except (KeyError, ZeroDivisionError, TypeError) as e:
            logger.error(f"Error calculating net_sales period_3: {e}")

        try:
            # Operating profit
            indicators['variability']['period_3']['operating_profit'] = float('{:.1f}'.format(
                ((period3['stateOfResult']['operating_profit'] - period2['stateOfResult']['operating_profit']) /
                 period2['stateOfResult']['operating_profit']) * 100
            ))
        except (KeyError, ZeroDivisionError, TypeError) as e:
            logger.error(f"Error calculating operating_profit period_3: {e}")

        try:
            # Net income
            indicators['variability']['period_3']['net_income'] = float('{:.1f}'.format(
                ((period3['stateOfResult']['net_income'] - period2['stateOfResult']['net_income']) /
                 period2['stateOfResult']['net_income']) * 100
            ))
        except (KeyError, ZeroDivisionError, TypeError) as e:
            logger.error(f"Error calculating net_income period_3: {e}")

        try:
            # Total assets
            indicators['variability']['period_3']['total_assets'] = float('{:.1f}'.format(
                ((period3['assets']['total_assets'] - period2['assets']['total_assets']) /
                 period2['assets']['total_assets']) * 100
            ))
        except (KeyError, ZeroDivisionError, TypeError) as e:
            logger.error(f"Error calculating total_assets period_3: {e}")

        try:
            # Total passives
            indicators['variability']['period_3']['total_passives'] = float('{:.1f}'.format(
                ((period3['passives']['total_passives'] - period2['passives']['total_passives']) /
                 period2['passives']['total_passives']) * 100
            ))
        except (KeyError, ZeroDivisionError, TypeError) as e:
            logger.error(f"Error calculating total_passives period_3: {e}")

        try:
            # Total patrimony
            indicators['variability']['period_3']['total_patrimony'] = float('{:.1f}'.format(
                ((period3['patrimony']['total_patrimony'] - period2['patrimony']['total_patrimony']) /
                 period2['patrimony']['total_patrimony']) * 100
            ))
        except (KeyError, ZeroDivisionError, TypeError) as e:
            logger.error(f"Error calculating total_patrimony period_3: {e}")

    logger.debug(f"'indicators calcVariability': {indicators}")
    return indicators
