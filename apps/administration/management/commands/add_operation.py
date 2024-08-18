import os
import pandas as pd
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.operation.models import PreOperation
from apps.bills.models import Bill
from apps.accounts.models import Account
class Command(BaseCommand):
    help = 'Crea nuevos registros desde un archivo Excel aplicando descuentos en la cuenta del inversionista'

    def handle(self, *args, **kwargs):
        excel_file_path = os.path.join(settings.BASE_DIR, 'apps/administration/management/commands/add_operation/file.xlsx')
        df = pd.read_excel(excel_file_path)

        with transaction.atomic():
            for index, row in df.iterrows():
                try:
                    # Validar que la factura existe
                    bill_id = row['bill_id']
                    amount_to_negotiate = row['amount']

                    bill = Bill.objects.filter(id=bill_id).first()
                    if not bill:
                        self.stderr.write(f'Error en la fila {index + 1}: La factura con id {bill_id} no existe.')
                        continue  # Salta a la siguiente fila

                    # Validar que el monto a negociar no excede el currentBalance
                    if amount_to_negotiate > bill.currentBalance:
                        self.stderr.write(f'Error en la fila {index + 1}: El monto a negociar ({amount_to_negotiate}) excede el saldo disponible ({bill.currentBalance}) para la factura con id {bill_id}.')
                        continue  # Salta a la siguiente fila

                    # Obtener la cuenta del inversionista relacionada con ClientAccount
                    client_account_id = row['clientAccount_id']
                    account = Account.objects.filter(id=client_account_id).first()
                    if not account:
                        self.stderr.write(f'Error en la fila {index + 1}: La cuenta del inversionista con id {client_account_id} no existe.')
                        continue  # Salta a la siguiente fila

                    # Descontar los montos del saldo de la cuenta del inversionista
                    present_value_investor = row['presentValueInvestor']
                    gm_value = row['GM']

                    # Validar si el saldo es suficiente
                    if account.balance < present_value_investor + gm_value:
                        self.stderr.write(f'Error en la fila {index + 1}: Saldo insuficiente en la cuenta del inversionista ({account.balance}) para descontar {present_value_investor + gm_value}.')
                        continue  # Salta a la siguiente fila

                    account.balance -= (present_value_investor + gm_value)
                    account.save()

                    # Crear un nuevo objeto PreOperation
                    obj = PreOperation.objects.create(
                        state=row['state'],
                        created_at=row['created_at'],
                        updated_at=row['updated_at'],
                        opId=row['opId'],
                        opDate=row['opDate'],
                        applyGm=row['applyGm'],
                        billFraction=row['billFraction'],
                        DateBill=row['DateBill'],
                        DateExpiration=row['DateExpiration'],
                        probableDate=row['probableDate'],
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
                        user_created_at_id=row['user_created_at_id'],
                        user_updated_at_id=row['user_updated_at_id'],
                        opPendingAmount=row['opPendingAmount'],
                        payedPercent=row['payedPercent'],
                        opExpiration=row['opExpiration'],
                        insufficientAccountBalance=row['insufficientAccountBalance'],
                        isRebuy=row['isRebuy'],
                    )

                    self.stdout.write(f'Se ha creado un nuevo registro con id {obj.id}')

                except Exception as e:
                    self.stderr.write(f'Error en la fila {index + 1}: {str(e)}')

        self.stdout.write(self.style.SUCCESS('Datos creados y descuentos aplicados correctamente'))
