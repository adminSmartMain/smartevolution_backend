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

def calcFinancialRisk(indicators, index, period):

    indicators['financialRisk'][f'period_{index + 1}']['period'] = period['period']

    if period['assets']['current_assets'] > 0 and  period['passives']['current_liabilities'] > 0:
   
        indicators['financialRisk'][f'period_{index + 1}']['currentReason'] = float('{:.1f}'.format(period['assets']['current_assets'] / period['passives']['current_liabilities']))
    else:
 
        indicators['financialRisk'][f'period_{index + 1}']['currentReason'] = 0

    indicators['financialRisk'][f'period_{index + 1}']['workingCapital'] = float('{:.1f}'.format(period['assets']['current_assets'] - period['passives']['current_liabilities']))

    if period['passives']['total_passives'] > 0 and  period['assets']['total_assets'] > 0:
   
        indicators['financialRisk'][f'period_{index + 1}']['debt'] = float('{:.1f}'.format((period['passives']['total_passives'] / period['assets']['total_assets']) * 100))
    else:

        indicators['financialRisk'][f'period_{index + 1}']['debt'] = 0
   
    if period['stateOfResult']['financial_expenses'] > 0 and (period['passives']['financial_obligation_cp'] + period['passives']['financial_obligation_lp'] ) > 0:
     
        indicators['financialRisk'][f'period_{index + 1}']['avgFinancialDebt'] = float('{:.1f}'.format((period['stateOfResult']['financial_expenses'] / (period['passives']['financial_obligation_cp'] + period['passives']['financial_obligation_lp'] )) * 100))
    else:
    
        indicators['financialRisk'][f'period_{index + 1}']['avgFinancialDebt'] = 0
 
    
    # Obtiene los valores necesarios y evita acceder a una clave inexistente
    financial_obligation_cp = period['passives'].get('financial_obligation_cp', 0)
    financial_obligation_lp = period['passives'].get('financial_obligation_lp', 0)
    ebitda = indicators['rentability'][f'period_{index + 1}'].get('EBITDA', 0)
    # Asegurar que EBITDA y la suma de las obligaciones financieras sean mayores que cero antes de dividir
    if ebitda > 0 and (financial_obligation_cp + financial_obligation_lp) > 0:
        indicators['financialRisk'][f'period_{index + 1}']['financialDebt_EBITDA'] = float(
            '{:.1f}'.format(((financial_obligation_cp + financial_obligation_lp) / ebitda) * 100)
        )
    else:
        # Asigna 0 si no es posible calcular el indicador
        indicators['financialRisk'][f'period_{index + 1}']['financialDebt_EBITDA'] = 0

    if indicators['rentability'][f'period_{index + 1}']['EBITDA'] > 0 and  period['stateOfResult']['financial_expenses'] > 0: 

        indicators['financialRisk'][f'period_{index + 1}']['EBITDA_financialExpenses'] = float('{:.1f}'.format(indicators['rentability'][f'period_{index + 1}']['EBITDA'] / period['stateOfResult']['financial_expenses']))
    else:
    
        indicators['financialRisk'][f'period_{index + 1}']['EBITDA_financialExpenses'] = 0
  
    
    if indicators['rentability'][f'period_{index + 1}']['EBITDA'] > 0 and (period['stateOfResult']['financial_expenses'] + period['passives']['financial_obligation_cp']) > 0:
        indicators['financialRisk'][f'period_{index + 1}']['EBITDA_debtServices'] = float('{:.1f}'.format(indicators['rentability'][f'period_{index + 1}']['EBITDA'] / (period['stateOfResult']['financial_expenses'] + period['passives']['financial_obligation_cp'])))
    else:
        indicators['financialRisk'][f'period_{index + 1}']['EBITDA_debtServices']=0

    if period['patrimony']['total_patrimony'] > 0:

        indicators['financialRisk'][f'period_{index + 1}']['payedCapital_prim_totalPatrimony'] = float('{:.1f}'.format(
            (period['patrimony']['payed_capital'] + period['patrimony']['sup_capital_prima']) / 
            period['patrimony']['total_patrimony'] * 100))

    else:
        
    
        indicators['financialRisk'][f'period_{index + 1}']['payedCapital_prim_totalPatrimony'] = 0
    return indicators