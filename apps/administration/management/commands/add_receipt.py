import os
import pandas as pd
from django.core.management.base import BaseCommand
from apps.operation.models import Receipt
from django.conf import settings
from apps.operation.models import PreOperation

class Command(BaseCommand):
    help = 'Import receipts from an Excel file into the Receipt model'

    def handle(self, *args, **kwargs):
        file_path = os.path.join(settings.BASE_DIR, 'apps/administration/management/commands/add_receipt/file.xlsx')
        
        # Leer el archivo Excel utilizando pandas
        try:
            data = pd.read_excel(file_path)
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error reading Excel file: {e}"))
            return
        
        # Iterar sobre las filas del DataFrame y crear instancias del modelo
        receipts_to_create = []
        for _, row in data.iterrows():
            # Buscar la operación correspondiente
            try:
                operation = PreOperation.objects.get(id=row['operation_id'])
            except PreOperation.DoesNotExist:
                self.stderr.write(self.style.ERROR(f"Operation with id {row['operation_id']} does not exist"))
                continue

            receipt = Receipt(
                id=row['id'],
                state=row['state'],
                created_at=row['created_at'],
                updated_at=row['updated_at'],
                date=row['date'],
                dId=row['dId'],
                typeReceipt_id=row['typeReceipt_id'],
                payedAmount=row['payedAmount'],
                investorInterests=row['investorInterests'],
                tableInterests=row['tableInterests'],
                additionalDays=row['additionalDays'],
                operation_id=row['operation_id'],
                user_created_at_id=row['user_created_at_id'],
                user_updated_at_id=row['user_updated_at_id'],
                additionalInterests=row['additionalInterests'],
                additionalInterestsSM=row['additionalInterestsSM'],
                futureValueRecalculation=row['futureValueRecalculation'],
                tableRemaining=row['tableRemaining'],
                realDays=row['realDays'],
                account_id=row['account_id'],
                calculatedDays=row['calculatedDays'],
                remaining=row['remaining'],
                receiptStatus_id=row['receiptStatus_id'],
                presentValueInvestor=row['presentValueInvestor']
            )
            receipts_to_create.append(receipt)
            
            # Regla de negocio 1: Actualizar el valor de opPendingAmount
            pending_amount_to_subtract = row['payedAmount']  # Puedes ajustar la lógica según la regla de negocio exacta
            operation.opPendingAmount -= pending_amount_to_subtract
            self.stdout.write(self.style.WARNING(f"Operation {operation.id} se esta restando la infomacion."))

            #operation.save()

            # Regla de negocio 2: Actualizar el status a 4 si el pendiente por cobrar es 0
            if operation.opPendingAmount <= 0:
                operation.status = 4
                self.stdout.write(self.style.WARNING(f"Operation {operation.id} el pendiente por cobrar es <= 0"))

            #    operation.save()
            
        # Insertar todos los registros en la base de datos de una sola vez
        try:
            #Receipt.objects.bulk_create(receipts_to_create)
            self.stdout.write(self.style.SUCCESS(f"Successfully imported {len(receipts_to_create)} receipts"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error saving to database: {e}"))            
        

