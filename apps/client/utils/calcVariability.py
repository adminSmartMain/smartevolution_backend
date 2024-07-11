def calcVariability(indicators, period1, period2=None, period3=None):
    #period 2 variability
    if period2 != None:
        indicators['variability']['period_2']['period'] = period2['period'] 
        indicators['variability']['period_2']['net_sales'] = float('{:.1f}'.format(((period1['stateOfResult']['net_sales'] - \
            period2['stateOfResult']['net_sales']) / period1['stateOfResult']['net_sales']) * -100))
        indicators['variability']['period_2']['operating_profit'] = float('{:.1f}'.format(((period1['stateOfResult']['operating_profit'] -
            period2['stateOfResult']['operating_profit']) / period1['stateOfResult']['operating_profit']) * -100))
        indicators['variability']['period_2']['net_income'] = float('{:.1f}'.format(((period1['stateOfResult']['net_income'] -
            period2['stateOfResult']['net_income']) / period1['stateOfResult']['net_income']) * -100))
        indicators['variability']['period_2']['total_assets'] = float('{:.1f}'.format(((period1['assets']['total_assets'] -
            period2['assets']['total_assets']) / period1['assets']['total_assets']) * -100))
        indicators['variability']['period_2']['total_passives'] = float('{:.1f}'.format(((period1['passives']['total_passives'] -
            period2['passives']['total_passives']) / period1['passives']['total_passives']) * -100))
        indicators['variability']['period_2']['total_patrimony'] = float('{:.1f}'.format(((period1['patrimony']['total_patrimony'] -
            period2['patrimony']['total_patrimony']) / period1['patrimony']['total_patrimony']) * -100))
    if period3 != None:    
        #period 3 variability
        indicators['variability']['period_3']['period']    = period1['period']
        indicators['variability']['period_3']['net_sales'] = float('{:.1f}'.format(((period2['stateOfResult']['net_sales'] - \
            period1['stateOfResult']['net_sales']) / period2['stateOfResult']['net_sales']) * -100))

        indicators['variability']['period_3']['operating_profit'] = float('{:.1f}'.format(((period2['stateOfResult']['operating_profit'] -
            period1['stateOfResult']['operating_profit']) / period2['stateOfResult']['operating_profit']) * -100))

        indicators['variability']['period_3']['net_income'] = float('{:.1f}'.format(((period2['stateOfResult']['net_income'] -
            period1['stateOfResult']['net_income']) / period2['stateOfResult']['net_income']) * -100))

        indicators['variability']['period_3']['total_assets'] = float('{:.1f}'.format(((period2['assets']['total_assets'] -
            period1['assets']['total_assets']) / period2['assets']['total_assets']) * -100))

        indicators['variability']['period_3']['total_passives'] = float('{:.1f}'.format(((period2['passives']['total_passives'] -
            period1['passives']['total_passives']) / period2['passives']['total_passives']) * -100))

        indicators['variability']['period_3']['total_patrimony'] = float('{:.1f}'.format(((period2['patrimony']['total_patrimony'] -
            period1['patrimony']['total_patrimony']) / period2['patrimony']['total_patrimony']) * -100))

    return indicators