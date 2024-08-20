import os
import pandas as pd
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.operation.models import PreOperation
from apps.bill.models import Bill
from apps.client.models import Account
from apps.base.utils.index import gen_uuid

class Command(BaseCommand):
    help = 'Crea nuevos registros desde un archivo Excel aplicando descuentos en la cuenta del inversionista'

    def handle(self, *args, **kwargs):
        excel_file_path = os.path.join(settings.BASE_DIR, 'apps/administration/management/commands/add_operation/file.xlsx')
        df = pd.read_excel(excel_file_path)

        # Asegúrate de que todas las columnas de fecha estén formateadas correctamente
        date_columns = [
            'created_at', 'updated_at', 'opDate', 'DateBill', 
            'DateExpiration', 'probableDate', 'opExpiration'
        ]
        
        for col in date_columns:
            df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%Y-%m-%d')

        for index, row in df.iterrows():
            try:
                with transaction.atomic():
                    #self.stderr.write(f'Fila {index + 1}: {row}.')

                    bill_id = row['bill_id']
                    amount_to_negotiate = row['amount']

                    bill = Bill.objects.filter(id=bill_id).first()
                    if not bill:
                        self.stderr.write(f'Error en la fila {index + 1}: La factura con id {bill_id} no existe.')
                        continue

                    #if amount_to_negotiate > bill.currentBalance:
                    #    self.stderr.write(f'Error en la fila {index + 1}: El monto a negociar ({amount_to_negotiate}) excede el saldo disponible ({bill.currentBalance}) para la factura con id {bill_id}.')
                    #    continue

                    client_account_id = row['clientAccount_id']
                    account = Account.objects.filter(id=client_account_id).first()
                    if not account:
                        self.stderr.write(f'Error en la fila {index + 1}: La cuenta del inversionista con id {client_account_id} no existe.')
                        continue

                    present_value_investor = row['presentValueInvestor']
                    gm_value = row['GM']

                    account.balance -= (present_value_investor + gm_value)
                    account.save()

                    obj = PreOperation.objects.create(
                        id=gen_uuid(),
                        state=row['state'],
                        created_at=row['created_at'] if pd.notna(row['created_at']) else None,
                        updated_at=row['updated_at'] if pd.notna(row['updated_at']) else None,
                        opId=row['opId'],
                        opDate=row['opDate'] if pd.notna(row['opDate']) else None,
                        applyGm=row['applyGm'],
                        billFraction=row['billFraction'],
                        DateBill=row['DateBill'] if pd.notna(row['DateBill']) else None,
                        DateExpiration=row['DateExpiration'] if pd.notna(row['DateExpiration']) else None,
                        probableDate=row['probableDate'] if pd.notna(row['probableDate']) else None,
                        amount=amount_to_negotiate,
                        payedAmount=row['payedAmount'],
                        discountTax=row['discountTax'],
                        investorTax=row['investorTax'],
                        operationDays=row['operationDays'],
                        presentValueInvestor=present_value_investor,
                        presentValueSF=row['presentValueSF'],
                        investorProfit=row['investorProfit'],
                        commissionSF=row['commissionSF'],
                        GM=gm_value,
                        status=row['status'],
                        bill_id=bill_id,
                        clientAccount_id=client_account_id,
                        emitter_id=row['emitter_id'],
                        emitterBroker_id=row['emitterBroker_id'],
                        investor_id=row['investor_id'],
                        investorBroker_id=row['investorBroker_id'],
                        opType_id=row['opType_id'],
                        payer_id=row['payer_id'],
                        user_created_at_id=row['user_created_at_id'] if pd.notna(row['user_created_at_id']) else None,
                        user_updated_at_id=row['user_updated_at_id'] if pd.notna(row['user_updated_at_id']) else None,
                        opPendingAmount=row['opPendingAmount'],
                        payedPercent=row['payedPercent'],
                        opExpiration=row['opExpiration'] if pd.notna(row['opExpiration']) else None,
                        insufficientAccountBalance=row['insufficientAccountBalance'],
                        isRebuy=row['isRebuy'],
                    )

                    self.stdout.write(f'Se ha creado un nuevo registro con id {obj.id}')

            except Exception as e:
                self.stderr.write(f'Error en la fila {index + 1}: {str(e)}')

        self.stdout.write(self.style.SUCCESS('Datos creados y descuentos aplicados correctamente'))
