import os
import pandas as pd
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.bill.models import Bill

class Command(BaseCommand):
    help = 'Actualiza datos desde un archivo Excel'

    def handle(self, *args, **kwargs):
        excel_file_path = os.path.join(settings.BASE_DIR, 'apps/administration/management/commands/update_bills/file.xlsx')
        #excel_file_path = '/apps/administration/management/commands/update_bills/file.xlsx'  # Reemplaza con la ruta real
        df = pd.read_excel(excel_file_path)

        with transaction.atomic():
            for index, row in df.iterrows():
                obj_id = row['id']
                try:
                    obj = Bill.objects.get(id=obj_id)
                    obj.total = row['total']
                    obj.currentBalance = row['currentBalance']
                    obj.ret_fte = row['ret_fte']
                    obj.ret_ica = row['ret_ica']
                    obj.ret_iva = row['ret_iva']
                    obj.creditNotesValue = row['creditNotesValue']
                    obj.other_ret = row['other_ret']
                    obj.save()
                except Bill.DoesNotExist:
                    print(f'Objeto con id {obj_id} no encontrado')

        self.stdout.write(self.style.SUCCESS('Datos actualizados'))
