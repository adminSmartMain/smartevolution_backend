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

    if indicators['rentability'][f'period_{index + 1}']['EBITDA'] > 0:    
        indicators['financialRisk'][f'period_{index + 1}']['financialDebt_EBITDA'] = float('{:.1f}'.format(((period['passives']['financial_obligation_cp'] + period['passives']['financial_obligation_lp']) / indicators['rentability'][f'period_{index + 1}']['EBITDA']) * 100))
    else:
        indicators['financialRisk'][f'period_{index + 1}']['financialDebt_EBITDA'] = 0

    if indicators['rentability'][f'period_{index + 1}']['EBITDA'] > 0 and  period['stateOfResult']['financial_expenses'] > 0: 
        indicators['financialRisk'][f'period_{index + 1}']['EBITDA_financialExpenses'] = float('{:.1f}'.format(indicators['rentability'][f'period_{index + 1}']['EBITDA'] / period['stateOfResult']['financial_expenses']))
    else:
        indicators['financialRisk'][f'period_{index + 1}']['EBITDA_financialExpenses'] = 0

    if indicators['rentability'][f'period_{index + 1}']['EBITDA'] > 0:
        indicators['financialRisk'][f'period_{index + 1}']['EBITDA_debtServices'] = float('{:.1f}'.format(indicators['rentability'][f'period_{index + 1}']['EBITDA'] / (period['stateOfResult']['financial_expenses'] + period['passives']['financial_obligation_cp'])))
    else:
        indicators['financialRisk'][f'period_{index + 1}']['EBITDA_debtServices'] = 0

    if period['patrimony']['total_patrimony'] > 0:
        indicators['financialRisk'][f'period_{index + 1}']['payedCapital_prim_totalPatrimony'] = float('{:.1f}'.format((period['patrimony']['payed_capital']+period['patrimony']['sup_capital_prima']) / period['patrimony']['total_patrimony'] * 100))
    else:
        indicators['financialRisk'][f'period_{index + 1}']['payedCapital_prim_totalPatrimony'] = 0

    return indicators