def calcRentability(indicators, index, period):
    indicators['rentability'][f'period_{index + 1}']['period'] = period['period']
    if period['stateOfResult']['gross_profit'] > 0 and  period['stateOfResult']['net_sales'] > 0:
        indicators['rentability'][f'period_{index + 1}']['grossMargin'] = float('{:.1f}'.format((period['stateOfResult']['gross_profit'] / period['stateOfResult']['net_sales']) * 100))
    else:
        indicators['rentability'][f'period_{index + 1}']['grossMargin'] = 0

    if period['stateOfResult']['operating_profit'] > 0 and period['stateOfResult']['net_sales'] > 0:
        indicators['rentability'][f'period_{index + 1}']['operationalMargin'] = float('{:.1f}'.format(period['stateOfResult']['operating_profit'] / period['stateOfResult']['net_sales'] * 100))
    else:
        indicators['rentability'][f'period_{index + 1}']['operationalMargin'] = 0
        
    indicators['rentability'][f'period_{index + 1}']['EBITDA'] = float('{:.1f}'.format(period['stateOfResult']['operating_profit'] + period['stateOfResult']['dep_amortization']))

    if indicators['rentability'][f'period_{index + 1}']['EBITDA'] > 0 and period['stateOfResult']['gross_sale'] > 0:
        indicators['rentability'][f'period_{index + 1}']['EBITDAMargin'] = float('{:.1f}'.format((indicators['rentability'][f'period_{index + 1}']['EBITDA'] / period['stateOfResult']['gross_sale']) * 100))
    else:
        indicators['rentability'][f'period_{index + 1}']['EBITDAMargin'] = 0
    
    if period['stateOfResult']['net_income'] > 0 and period['stateOfResult']['gross_sale'] > 0:
        indicators['rentability'][f'period_{index + 1}']['netMargin'] = float('{:.1f}'.format(period['stateOfResult']['net_income'] / period['stateOfResult']['gross_sale'] * 100))
    else:
        indicators['rentability'][f'period_{index + 1}']['netMargin'] = 0

    if period['stateOfResult']['net_income'] > 0 and  period['assets']['total_assets'] > 0:
        indicators['rentability'][f'period_{index + 1}']['rentabilityTotalAssets'] = float('{:.1f}'.format(period['stateOfResult']['net_income'] / period['assets']['total_assets'] * 100))
    else:
        indicators['rentability'][f'period_{index + 1}']['rentabilityTotalAssets'] = 0
    
    if period['stateOfResult']['net_income'] > 0 and period['patrimony']['total_patrimony'] > 0:
        indicators['rentability'][f'period_{index + 1}']['patrimonyRentability'] = float('{:.1f}'.format(period['stateOfResult']['net_income'] / period['patrimony']['total_patrimony'] * 100))
    else:
        indicators['rentability'][f'period_{index + 1}']['patrimonyRentability'] = 0

    return indicators