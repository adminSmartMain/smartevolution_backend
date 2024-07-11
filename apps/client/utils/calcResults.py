def calcResults(indicators, index, period):
    periodDays = 0
    if period['typePeriod'] == '0835dcb5-d6f2-43d7-b7ca-8864119ea05f':
        periodDays = 365
    elif period['typePeriod'] == 'e635f0f1-b29c-45e5-b351-04725a489be3':
        periodDays = 181
    elif period['typePeriod'] == 'e7b663d7-5cc3-4a9f-b288-95ce38c1ccfd':
        periodDays = 90
    else:
        periodDays = period['periodDays']

    indicators['results'][f'period_{index + 1}']['period'] = period['period']       
    indicators['results'][f'period_{index + 1}']['sales'] = float('{:.1f}'.format(period['stateOfResult']['net_sales']))
    if period['stateOfResult']['net_sales'] > 0:
        indicators['results'][f'period_{index + 1}']['avgMonthBilling'] = float('{:.1f}'.format((period['stateOfResult']['net_sales']/(periodDays/30))))
    else:
        indicators['results'][f'period_{index + 1}']['avgMonthBilling'] = 0

    if period['stateOfResult']['dtos_returns'] > 0 and  period['stateOfResult']['gross_sale'] > 0:
        indicators['results'][f'period_{index + 1}']['discountsSalesRefunds'] = float('{:.1f}'.format((period['stateOfResult']['dtos_returns'] / period['stateOfResult']['gross_sale']) * 100))
    else:
        indicators['results'][f'period_{index + 1}']['discountsSalesRefunds'] = 0       
    return indicators