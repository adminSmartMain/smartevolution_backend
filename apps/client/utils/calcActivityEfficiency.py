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

def calcActivityEfficiency(indicators, index, period):

    periodDays = 0
    
    if period['typePeriod'] == '0835dcb5-d6f2-43d7-b7ca-8864119ea05f':
        periodDays = 360
    elif period['typePeriod'] == 'e635f0f1-b29c-45e5-b351-04725a489be3':
        periodDays = 180
    elif period['typePeriod'] == 'e7b663d7-5cc3-4a9f-b288-95ce38c1ccfd':
        periodDays = 90
    else:
        periodDays = period['periodDays']

    indicators['activityEfficiency'][f'period_{index + 1}']['period'] = period['period']
    if period['assets']['clients_wallet'] > 0 and  period['stateOfResult']['gross_sale'] > 0:
        indicators['activityEfficiency'][f'period_{index + 1}']['walletRotation'] = float('{:.1f}'.format((period['assets']['clients_wallet'] / period['stateOfResult']['gross_sale']) * periodDays))
    else:
        indicators['activityEfficiency'][f'period_{index + 1}']['walletRotation'] = 0

    if period['assets']['total_inventory'] > 0 and  period['stateOfResult']['cost_of_sales'] > 0:
        indicators['activityEfficiency'][f'period_{index + 1}']['inventoryRotation'] = float('{:.1f}'.format((period['assets']['total_inventory'] / period['stateOfResult']['cost_of_sales']) * periodDays))
    else:
        indicators['activityEfficiency'][f'period_{index + 1}']['inventoryRotation'] = 0


    indicators['activityEfficiency'][f'period_{index + 1}']['operationalCycle'] = float('{:.1f}'.format(indicators['activityEfficiency'][f'period_{index + 1}']['walletRotation'] + indicators['activityEfficiency'][f'period_{index + 1}']['inventoryRotation']))

    if period['passives']['providers'] > 0 and period['stateOfResult']['net_sales'] > 0:
        indicators['activityEfficiency'][f'period_{index + 1}']['providersRotation'] = float('{:.1f}'.format((period['passives']['providers'] / period['stateOfResult']['net_sales']) * periodDays))
    else:
        indicators['activityEfficiency'][f'period_{index + 1}']['providersRotation'] = 0

    if period['passives']['unpaid_expenses'] > 0 and period['stateOfResult']['net_sales'] > 0:
        indicators['activityEfficiency'][f'period_{index + 1}']['accumulatedExpensesRotation'] = float('{:.1f}'.format((period['passives']['unpaid_expenses'] / period['stateOfResult']['net_sales']) * periodDays))
    else:
        indicators['activityEfficiency'][f'period_{index + 1}']['accumulatedExpensesRotation'] = 0


    indicators['activityEfficiency'][f'period_{index + 1}']['cashConversionCycle'] = float('{:.1f}'.format((indicators['activityEfficiency'][f'period_{index + 1}']['inventoryRotation'] - indicators['activityEfficiency'][f'period_{index + 1}']['accumulatedExpensesRotation'] + indicators['activityEfficiency'][f'period_{index + 1}']['walletRotation'])))

    if period['stateOfResult']['gross_sale'] > 0 and period['patrimony']['passive_and_patrimony'] > 0:
        indicators['activityEfficiency'][f'period_{index + 1}']['assetsRotation'] = float('{:.1f}'.format(period['stateOfResult']['gross_sale'] / period['patrimony']['passive_and_patrimony']))
    else:
        indicators['activityEfficiency'][f'period_{index + 1}']['assetsRotation'] = 0

    
   

    return indicators