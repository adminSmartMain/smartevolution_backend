import pandas as pd
import uuid
import json
from datetime import datetime
# Read the tablas.xlsx file and get the CORREDORES sheet
df = pd.read_excel('tablas.xlsx', sheet_name='PERFIL FINANCIERO')
# convert all rows to a list of dictionaries
data = df.to_dict('records')
financialProfiles = []

for row in data:
    clientId = row['ID_CL']
    clientName = row['NOMBRE_CL']
    # get the date and extract the year
    date1 = row['FECHA1']
    year1 = date1.year
    startDate1 = date1 - pd.DateOffset(days=row['DIAS1'])
    date1 = date1.strftime('%Y-%m-%d')
    startDate1 = startDate1.strftime('%Y-%m-%d')
    date2 = row['FECHA2']
    year2 = date2.year
    startDate2 = date2 - pd.DateOffset(days=row['DIAS2'])
    date2 = date2.strftime('%Y-%m-%d')
    startDate2 = startDate2.strftime('%Y-%m-%d')
    try:
        date3 = row['FECHA3']
        year3 = date3.year
        startDate3 = date3 - pd.DateOffset(days=row['DIAS3'])
        date3 = date3.strftime('%Y-%m-%d')
        startDate3 = startDate3.strftime('%Y-%m-%d')
        period3 = {
        'id': str(uuid.uuid4()),
        'period': year3,
        'client': clientId,
        'clientName': clientName,
        'typePeriod': 'a32eec8b-06e3-4fbc-a888-d33364032353',
        'periodRange': None,
        'periodDays': row['DIAS3'],
        'periodStartDate': startDate3,
        'periodEndDate': date3,
        'assets': {
            'id': str(uuid.uuid4()),
            'cash_and_investments': row['CAJA_INVERS3'],
            'clients_wallet': row['CARTERA3'],
            'cxc_partners': row['CC_SOCIOS3'],
            'other_cxc': row['CC_OTROS3'],
            'net_cxc': row['CARTERA3'] + row['CC_SOCIOS3'] + row['CC_OTROS3'],
            'raw_material_and_others': row['MAT_PRIMA3'],
            'products_finished': row['PROD_TERM3'],
            'total_inventory': row['MAT_PRIMA3'] + row['PROD_TERM3'],
            'advances_and_progress': row['ANTIC_AVANC3'],
            'current_assets': row['CAJA_INVERS3'] + row['ANTIC_AVANC3'] + row['CARTERA3'] + row['CC_SOCIOS3'] + row['CC_OTROS3'] + row['MAT_PRIMA3'] + row['PROD_TERM3'],
            'lands_and_buildings': row['TERRENOS_EDF3'],
            'm_and_e_vehicles': row['MOB_EQP_VEHIC3'],
            'gross_fixed_assets': row['TERRENOS_EDF3'] + row['MOB_EQP_VEHIC3'],
            'dep_acum': row['DEP_ACUM3'],
            'net_fixed_assets': (row['TERRENOS_EDF3'] - row['MOB_EQP_VEHIC3']) - row['DEP_ACUM3'],
            'difer_intang_leasing': row['DIF_INTANG_LEASING3'],
            'investments_and_others': row['INV_PTES_OTROS3'],
            'total_other_assets': row['DIF_INTANG_LEASING3'] + row['INV_PTES_OTROS3'],
            'total_assets': row['CAJA_INVERS3'] + row['ANTIC_AVANC3'] + row['CARTERA3'] +
            row['CC_SOCIOS3'] + row['CC_OTROS3'] + row['MAT_PRIMA3'] + row['PROD_TERM3'] +
            row['TERRENOS_EDF3'] + row['MOB_EQP_VEHIC3'] + row['DIF_INTANG_LEASING3'] +
            row['INV_PTES_OTROS3'] - row['DEP_ACUM3']
        },
        'passives': {
            'id': str(uuid.uuid4()),
            'financial_obligation_cp': row['OBLG_FINANC_CP3'],
            'providers': row['PROVEEDORES3'],
            'unpaid_expenses': row['GASTOS_PP3'],
            'unpaid_taxes': row['IMP_PP3'],
            'linked_economics': row['VINC_ECON3'],
            'estimated_passives': row['PASIVOS_ESTM_PROV3'],
            'current_liabilities': row['OBLG_FINANC_CP3'] + row['PROVEEDORES3'] + row['GASTOS_PP3'] + row['IMP_PP3'] +
            row['VINC_ECON3'] + row['PASIVOS_ESTM_PROV3'],
            'financial_obligation_lp': row['OBLG_FINAC_LP3'],
            'other_lp_leasing': row['OTROS_LP_LEASING3'],
            'lp_passives': row['OBLG_FINAC_LP3'] + row['OTROS_LP_LEASING3'],
            'total_passives': row['OBLG_FINANC_CP3'] + row['PROVEEDORES3'] + row['GASTOS_PP3'] + row['IMP_PP3'] +
            row['VINC_ECON3'] + row['PASIVOS_ESTM_PROV3'] +
            row['OBLG_FINAC_LP3'] + row['OTROS_LP_LEASING3']
        },
        'patrimony': {
            'id': str(uuid.uuid4()),
            'payed_capital': row['CAPITAL_PAGADO3'],
            'sup_capital_prima': row['SUP_CAPITAL_PRIM3'],
            'legal_reserve': row['RESERV_LEGAL3'],
            'periods_results': row['RESULT_PERIOD3'],
            'accumulated_results': row['RESULT_ACUM3'],
            'rev_patrimony_niif': row['REV_PATRIM_NIIF3'],
            'total_patrimony': row['CAPITAL_PAGADO3'] + row['SUP_CAPITAL_PRIM3'] + row['RESERV_LEGAL3'] + row['RESULT_PERIOD3'] + row['RESULT_ACUM3'] + row['REV_PATRIM_NIIF3'],
            'passive_and_patrimony': (row['OBLG_FINANC_CP3'] + row['PROVEEDORES3'] + row['GASTOS_PP3'] + row['IMP_PP3'] +
                                      row['VINC_ECON3'] + row['PASIVOS_ESTM_PROV3'] + row['OBLG_FINAC_LP3'] +
                                      row['OTROS_LP_LEASING3']+row['CAPITAL_PAGADO3'] + row['SUP_CAPITAL_PRIM3'] +
                                      row['RESERV_LEGAL3'] + row['RESULT_PERIOD3'] + row['RESULT_ACUM3'] + row['REV_PATRIM_NIIF3']) -
                                     (row['CAJA_INVERS3'] + row['ANTIC_AVANC3'] + row['CARTERA3'] + row['CC_SOCIOS3'] +
                                      row['CC_OTROS3'] + row['MAT_PRIMA3'] +
                                      row['PROD_TERM3'] + row['TERRENOS_EDF3']
                                      + row['MOB_EQP_VEHIC3'] + row['DEP_ACUM3'] + row['DIF_INTANG_LEASING3'] + row['INV_PTES_OTROS3']),
            'total_assets_passives': (row['OBLG_FINANC_CP3'] + row['PROVEEDORES3'] + row['GASTOS_PP3'] +
                                      row['IMP_PP3'] + row['VINC_ECON3'] + row['PASIVOS_ESTM_PROV3'] + row['OBLG_FINAC_LP3'] +
                                      row['OTROS_LP_LEASING3'] + row['CAPITAL_PAGADO3'] + row['SUP_CAPITAL_PRIM3'] +
                                      row['RESERV_LEGAL3'] + row['RESULT_PERIOD3'] + row['RESULT_ACUM3'] + row['REV_PATRIM_NIIF3']) -
            (row['CAJA_INVERS3'] + row['ANTIC_AVANC3'] + row['CARTERA3'] + row['CC_SOCIOS3'] +
             row['CC_OTROS3'] + row['MAT_PRIMA3'] + row['PROD_TERM3'] + row['TERRENOS_EDF3'] +
             row['MOB_EQP_VEHIC3'] + row['DEP_ACUM3'] + row['DIF_INTANG_LEASING3'] + row['INV_PTES_OTROS3'])
        },
        'stateOfResult': {
            'id': str(uuid.uuid4()),
            'gross_sale': row['VTAS_BRUTAS3'],
            'dtos_returns': row['DTOS_DEVOLUC3'],
            'net_sales': row['VTAS_BRUTAS3'] + row['DTOS_DEVOLUC3'],
            'cost_of_sales': row['COSTOS_VTAS3'],
            'gross_profit': row['VTAS_BRUTAS3'] - row['DTOS_DEVOLUC3'] - row['COSTOS_VTAS3'],
            'administrative_expenses_sales': row['GASTOS_ADM_VTAS3'],
            'dep_amortization': row['DEP_AUT3'],
            'operating_profit': row['VTAS_BRUTAS3'] - row['DTOS_DEVOLUC3'] - row['COSTOS_VTAS3'] - (row['GASTOS_ADM_VTAS3'] + row['DEP_AUT3']),
            'financial_income': row['ING_FINANC3'],
            'other_incomes': row['OTROS_ING3'],
            'financial_expenses': row['GASTOS_FINANC3'],
            'other_expenditures': row['OTROS_EGR3'],
            'income_before_taxes': row['VTAS_BRUTAS3'] - row['DTOS_DEVOLUC3'] - row['COSTOS_VTAS3'] - (row['GASTOS_ADM_VTAS3'] + row['DEP_AUT3']) + row['ING_FINANC3'] -
            row['OTROS_ING3'] - row['GASTOS_FINANC3'] - row['OTROS_EGR3'],
            'provision_for_taxes': row['PROV_IMP3'],
            'net_income': row['VTAS_BRUTAS3'] - row['DTOS_DEVOLUC3'] - row['COSTOS_VTAS3'] - (row['GASTOS_ADM_VTAS3'] + row['DEP_AUT3']) +
            row['ING_FINANC3'] + row['OTROS_ING3'] -
            row['GASTOS_FINANC3'] - row['OTROS_EGR3'] - row['PROV_IMP3']
        }
    }
    except:
        period3 = None
    # Parse the first period
    period1 = {
        'id': str(uuid.uuid4()),
        'period': year1,
        'client': clientId,
        'clientName': clientName,
        'typePeriod': 'a12eec8b-06e1-4fbc-a888-d33364032151',
        'periodRange': None,
        'periodDays': row['DIAS1'],
        'periodStartDate': startDate1,
        'periodEndDate': date1,
        'assets': {
            'id': str(uuid.uuid4()),
            'cash_and_investments': row['CAJA_INVERS1'],
            'clients_wallet': row['CARTERA1'],
            'cxc_partners': row['CC_SOCIOS1'],
            'other_cxc': row['CC_OTROS1'],
            'net_cxc': row['CARTERA1'] + row['CC_SOCIOS1'] + row['CC_OTROS1'],
            'raw_material_and_others': row['MAT_PRIMA1'],
            'products_finished': row['PROD_TERM1'],
            'total_inventory': row['MAT_PRIMA1'] + row['PROD_TERM1'],
            'advances_and_progress': row['ANTIC_AVANC1'],
            'current_assets': row['CAJA_INVERS1'] + row['ANTIC_AVANC1'] + row['CARTERA1'] + row['CC_SOCIOS1'] + row['CC_OTROS1'] + row['MAT_PRIMA1'] + row['PROD_TERM1'],
            'lands_and_buildings': row['TERRENOS_EDF1'],
            'm_and_e_vehicles': row['MOB_EQP_VEHIC1'],
            'gross_fixed_assets': row['TERRENOS_EDF1'] + row['MOB_EQP_VEHIC1'],
            'dep_acum': row['DEP_ACUM1'],
            'net_fixed_assets': (row['TERRENOS_EDF1'] - row['MOB_EQP_VEHIC1']) - row['DEP_ACUM1'],
            'difer_intang_leasing': row['DIF_INTANG_LEASING1'],
            'investments_and_others': row['INV_PTES_OTROS1'],
            'total_other_assets': row['DIF_INTANG_LEASING1'] + row['INV_PTES_OTROS1'],
            'total_assets': row['CAJA_INVERS1'] + row['ANTIC_AVANC1'] + row['CARTERA1'] +
            row['CC_SOCIOS1'] + row['CC_OTROS1'] + row['MAT_PRIMA1'] + row['PROD_TERM1'] +
            row['TERRENOS_EDF1'] + row['MOB_EQP_VEHIC1'] + row['DIF_INTANG_LEASING1'] +
            row['INV_PTES_OTROS1'] - row['DEP_ACUM1']
        },
        'passives': {
            'id': str(uuid.uuid4()),
            'financial_obligation_cp': row['OBLG_FINANC_CP1'],
            'providers': row['PROVEEDORES1'],
            'unpaid_expenses': row['GASTOS_PP1'],
            'unpaid_taxes': row['IMP_PP1'],
            'linked_economics': row['VINC_ECON1'],
            'estimated_passives': row['PASIVOS_ESTM_PROV1'],
            'current_liabilities': row['OBLG_FINANC_CP1'] + row['PROVEEDORES1'] + row['GASTOS_PP1'] + row['IMP_PP1'] +
            row['VINC_ECON1'] + row['PASIVOS_ESTM_PROV1'],
            'financial_obligation_lp': row['OBLG_FINAC_LP1'],
            'other_lp_leasing': row['OTROS_LP_LEASING1'],
            'lp_passives': row['OBLG_FINAC_LP1'] + row['OTROS_LP_LEASING1'],
            'total_passives': row['OBLG_FINANC_CP1'] + row['PROVEEDORES1'] + row['GASTOS_PP1'] + row['IMP_PP1'] +
            row['VINC_ECON1'] + row['PASIVOS_ESTM_PROV1'] +
            row['OBLG_FINAC_LP1'] + row['OTROS_LP_LEASING1']
        },
        'patrimony': {
            'id': str(uuid.uuid4()),
            'payed_capital': row['CAPITAL_PAGADO1'],
            'sup_capital_prima': row['SUP_CAPITAL_PRIM1'],
            'legal_reserve': row['RESERV_LEGAL1'],
            'periods_results': row['RESULT_PERIOD1'],
            'accumulated_results': row['RESULT_ACUM1'],
            'rev_patrimony_niif': row['REV_PATRIM_NIIF1'],
            'total_patrimony': row['CAPITAL_PAGADO1'] + row['SUP_CAPITAL_PRIM1'] + row['RESERV_LEGAL1'] + row['RESULT_PERIOD1'] + row['RESULT_ACUM1'] + row['REV_PATRIM_NIIF1'],
            'passive_and_patrimony': (row['OBLG_FINANC_CP1'] + row['PROVEEDORES1'] + row['GASTOS_PP1'] + row['IMP_PP1'] +
                                      row['VINC_ECON1'] + row['PASIVOS_ESTM_PROV1'] + row['OBLG_FINAC_LP1'] +
                                      row['OTROS_LP_LEASING1']+row['CAPITAL_PAGADO1'] + row['SUP_CAPITAL_PRIM1'] +
                                      row['RESERV_LEGAL1'] + row['RESULT_PERIOD1'] + row['RESULT_ACUM1'] + row['REV_PATRIM_NIIF1']) -
                                     (row['CAJA_INVERS1'] + row['ANTIC_AVANC1'] + row['CARTERA1'] + row['CC_SOCIOS1'] +
                                      row['CC_OTROS1'] + row['MAT_PRIMA1'] +
                                      row['PROD_TERM1'] + row['TERRENOS_EDF1']
                                      + row['MOB_EQP_VEHIC1'] + row['DEP_ACUM1'] + row['DIF_INTANG_LEASING1'] + row['INV_PTES_OTROS1']),
            'total_assets_passives': (row['OBLG_FINANC_CP1'] + row['PROVEEDORES1'] + row['GASTOS_PP1'] +
                                      row['IMP_PP1'] + row['VINC_ECON1'] + row['PASIVOS_ESTM_PROV1'] + row['OBLG_FINAC_LP1'] +
                                      row['OTROS_LP_LEASING1'] + row['CAPITAL_PAGADO1'] + row['SUP_CAPITAL_PRIM1'] +
                                      row['RESERV_LEGAL1'] + row['RESULT_PERIOD1'] + row['RESULT_ACUM1'] + row['REV_PATRIM_NIIF1']) -
            (row['CAJA_INVERS1'] + row['ANTIC_AVANC1'] + row['CARTERA1'] + row['CC_SOCIOS1'] +
             row['CC_OTROS1'] + row['MAT_PRIMA1'] + row['PROD_TERM1'] + row['TERRENOS_EDF1'] +
             row['MOB_EQP_VEHIC1'] + row['DEP_ACUM1'] + row['DIF_INTANG_LEASING1'] + row['INV_PTES_OTROS1'])
        },
        'stateOfResult': {
            'id': str(uuid.uuid4()),
            'gross_sale': row['VTAS_BRUTAS1'],
            'dtos_returns': row['DTOS_DEVOLUC1'],
            'net_sales': row['VTAS_BRUTAS1'] + row['DTOS_DEVOLUC1'],
            'cost_of_sales': row['COSTOS_VTAS1'],
            'gross_profit': row['VTAS_BRUTAS1'] - row['DTOS_DEVOLUC1'] - row['COSTOS_VTAS1'],
            'administrative_expenses_sales': row['GASTOS_ADM_VTAS1'],
            'dep_amortization': row['DEP_AUT1'],
            'operating_profit': row['VTAS_BRUTAS1'] - row['DTOS_DEVOLUC1'] - row['COSTOS_VTAS1'] - (row['GASTOS_ADM_VTAS1'] + row['DEP_AUT1']),
            'financial_income': row['ING_FINANC1'],
            'other_incomes': row['OTROS_ING1'],
            'financial_expenses': row['GASTOS_FINANC1'],
            'other_expenditures': row['OTROS_EGR1'],
            'income_before_taxes': row['VTAS_BRUTAS1'] - row['DTOS_DEVOLUC1'] - row['COSTOS_VTAS1'] - (row['GASTOS_ADM_VTAS1'] + row['DEP_AUT1']) + row['ING_FINANC1'] -
            row['OTROS_ING1'] - row['GASTOS_FINANC1'] - row['OTROS_EGR1'],
            'provision_for_taxes': row['PROV_IMP1'],
            'net_income': row['VTAS_BRUTAS1'] - row['DTOS_DEVOLUC1'] - row['COSTOS_VTAS1'] - (row['GASTOS_ADM_VTAS1'] + row['DEP_AUT1']) +
            row['ING_FINANC1'] + row['OTROS_ING1'] -
            row['GASTOS_FINANC1'] - row['OTROS_EGR1'] - row['PROV_IMP1']
        }
    }

    period2 = {
        'id': str(uuid.uuid4()),
        'period': year2,
        'client': clientId,
        'clientName': clientName,
        'typePeriod': 'a22eec8b-06e2-4fbc-a888-d33364032252',
        'periodRange': None,
        'periodDays': row['DIAS2'],
        'periodStartDate': startDate2,
        'periodEndDate': date2,
        'assets': {
            'id': str(uuid.uuid4()),
            'cash_and_investments': row['CAJA_INVERS2'],
            'clients_wallet': row['CARTERA2'],
            'cxc_partners': row['CC_SOCIOS2'],
            'other_cxc': row['CC_OTROS2'],
            'net_cxc': row['CARTERA2'] + row['CC_SOCIOS2'] + row['CC_OTROS2'],
            'raw_material_and_others': row['MAT_PRIMA2'],
            'products_finished': row['PROD_TERM2'],
            'total_inventory': row['MAT_PRIMA2'] + row['PROD_TERM2'],
            'advances_and_progress': row['ANTIC_AVANC2'],
            'current_assets': row['CAJA_INVERS2'] + row['ANTIC_AVANC2'] + row['CARTERA2'] + row['CC_SOCIOS2'] + row['CC_OTROS2'] + row['MAT_PRIMA2'] + row['PROD_TERM2'],
            'lands_and_buildings': row['TERRENOS_EDF2'],
            'm_and_e_vehicles': row['MOB_EQP_VEHIC2'],
            'gross_fixed_assets': row['TERRENOS_EDF2'] + row['MOB_EQP_VEHIC2'],
            'dep_acum': row['DEP_ACUM2'],
            'net_fixed_assets': (row['TERRENOS_EDF2'] - row['MOB_EQP_VEHIC2']) - row['DEP_ACUM2'],
            'difer_intang_leasing': row['DIF_INTANG_LEASING2'],
            'investments_and_others': row['INV_PTES_OTROS2'],
            'total_other_assets': row['DIF_INTANG_LEASING2'] + row['INV_PTES_OTROS2'],
            'total_assets': row['CAJA_INVERS2'] + row['ANTIC_AVANC2'] + row['CARTERA2'] +
            row['CC_SOCIOS2'] + row['CC_OTROS2'] + row['MAT_PRIMA2'] + row['PROD_TERM2'] +
            row['TERRENOS_EDF2'] + row['MOB_EQP_VEHIC2'] + row['DIF_INTANG_LEASING2'] +
            row['INV_PTES_OTROS2'] - row['DEP_ACUM2']
        },
        'passives': {
            'id': str(uuid.uuid4()),
            'financial_obligation_cp': row['OBLG_FINANC_CP2'],
            'providers': row['PROVEEDORES2'],
            'unpaid_expenses': row['GASTOS_PP2'],
            'unpaid_taxes': row['IMP_PP2'],
            'linked_economics': row['VINC_ECON2'],
            'estimated_passives': row['PASIVOS_ESTM_PROV2'],
            'current_liabilities': row['OBLG_FINANC_CP2'] + row['PROVEEDORES2'] + row['GASTOS_PP2'] + row['IMP_PP2'] +
            row['VINC_ECON2'] + row['PASIVOS_ESTM_PROV2'],
            'financial_obligation_lp': row['OBLG_FINAC_LP2'],
            'other_lp_leasing': row['OTROS_LP_LEASING2'],
            'lp_passives': row['OBLG_FINAC_LP2'] + row['OTROS_LP_LEASING2'],
            'total_passives': row['OBLG_FINANC_CP2'] + row['PROVEEDORES2'] + row['GASTOS_PP2'] + row['IMP_PP2'] +
            row['VINC_ECON2'] + row['PASIVOS_ESTM_PROV2'] +
            row['OBLG_FINAC_LP2'] + row['OTROS_LP_LEASING2']
        },
        'patrimony': {
            'id': str(uuid.uuid4()),
            'payed_capital': row['CAPITAL_PAGADO2'],
            'sup_capital_prima': row['SUP_CAPITAL_PRIM2'],
            'legal_reserve': row['RESERV_LEGAL2'],
            'periods_results': row['RESULT_PERIOD2'],
            'accumulated_results': row['RESULT_ACUM2'],
            'rev_patrimony_niif': row['REV_PATRIM_NIIF2'],
            'total_patrimony': row['CAPITAL_PAGADO2'] + row['SUP_CAPITAL_PRIM2'] + row['RESERV_LEGAL2'] + row['RESULT_PERIOD2'] + row['RESULT_ACUM2'] + row['REV_PATRIM_NIIF2'],
            'passive_and_patrimony': (row['OBLG_FINANC_CP2'] + row['PROVEEDORES2'] + row['GASTOS_PP2'] + row['IMP_PP2'] +
                                      row['VINC_ECON2'] + row['PASIVOS_ESTM_PROV2'] + row['OBLG_FINAC_LP2'] +
                                      row['OTROS_LP_LEASING2']+row['CAPITAL_PAGADO2'] + row['SUP_CAPITAL_PRIM2'] +
                                      row['RESERV_LEGAL2'] + row['RESULT_PERIOD2'] + row['RESULT_ACUM2'] + row['REV_PATRIM_NIIF2']) -
                                     (row['CAJA_INVERS2'] + row['ANTIC_AVANC2'] + row['CARTERA2'] + row['CC_SOCIOS2'] +
                                      row['CC_OTROS2'] + row['MAT_PRIMA2'] +
                                      row['PROD_TERM2'] + row['TERRENOS_EDF2']
                                      + row['MOB_EQP_VEHIC2'] + row['DEP_ACUM2'] + row['DIF_INTANG_LEASING2'] + row['INV_PTES_OTROS2']),
            'total_assets_passives': (row['OBLG_FINANC_CP2'] + row['PROVEEDORES2'] + row['GASTOS_PP2'] +
                                      row['IMP_PP2'] + row['VINC_ECON2'] + row['PASIVOS_ESTM_PROV2'] + row['OBLG_FINAC_LP2'] +
                                      row['OTROS_LP_LEASING2'] + row['CAPITAL_PAGADO2'] + row['SUP_CAPITAL_PRIM2'] +
                                      row['RESERV_LEGAL2'] + row['RESULT_PERIOD2'] + row['RESULT_ACUM2'] + row['REV_PATRIM_NIIF2']) -
            (row['CAJA_INVERS2'] + row['ANTIC_AVANC2'] + row['CARTERA2'] + row['CC_SOCIOS2'] +
             row['CC_OTROS2'] + row['MAT_PRIMA2'] + row['PROD_TERM2'] + row['TERRENOS_EDF2'] +
             row['MOB_EQP_VEHIC2'] + row['DEP_ACUM2'] + row['DIF_INTANG_LEASING2'] + row['INV_PTES_OTROS2'])
        },
        'stateOfResult': {
            'id': str(uuid.uuid4()),
            'gross_sale': row['VTAS_BRUTAS2'],
            'dtos_returns': row['DTOS_DEVOLUC2'],
            'net_sales': row['VTAS_BRUTAS2'] + row['DTOS_DEVOLUC2'],
            'cost_of_sales': row['COSTOS_VTAS2'],
            'gross_profit': row['VTAS_BRUTAS2'] - row['DTOS_DEVOLUC2'] - row['COSTOS_VTAS2'],
            'administrative_expenses_sales': row['GASTOS_ADM_VTAS2'],
            'dep_amortization': row['DEP_AUT2'],
            'operating_profit': row['VTAS_BRUTAS2'] - row['DTOS_DEVOLUC2'] - row['COSTOS_VTAS2'] - (row['GASTOS_ADM_VTAS2'] + row['DEP_AUT2']),
            'financial_income': row['ING_FINANC2'],
            'other_incomes': row['OTROS_ING2'],
            'financial_expenses': row['GASTOS_FINANC2'],
            'other_expenditures': row['OTROS_EGR2'],
            'income_before_taxes': row['VTAS_BRUTAS2'] - row['DTOS_DEVOLUC2'] - row['COSTOS_VTAS2'] - (row['GASTOS_ADM_VTAS2'] + row['DEP_AUT2']) + row['ING_FINANC2'] -
            row['OTROS_ING2'] - row['GASTOS_FINANC2'] - row['OTROS_EGR2'],
            'provision_for_taxes': row['PROV_IMP2'],
            'net_income': row['VTAS_BRUTAS2'] - row['DTOS_DEVOLUC2'] - row['COSTOS_VTAS2'] - (row['GASTOS_ADM_VTAS2'] + row['DEP_AUT2']) +
            row['ING_FINANC2'] + row['OTROS_ING2'] -
            row['GASTOS_FINANC2'] - row['OTROS_EGR2'] - row['PROV_IMP2']
        }
    }

    financialProfiles.append(period1)
    financialProfiles.append(period2)
    financialProfiles.append(period3)

# create a json file
with open('financialProfiles.json', 'w') as outfile:
    json.dump(financialProfiles, outfile)