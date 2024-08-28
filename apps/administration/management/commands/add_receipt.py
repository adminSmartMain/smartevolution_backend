import os
import pandas as pd
import requests
from django.core.management.base import BaseCommand
from apps.operation.models import PreOperation
from django.conf import settings
import math

class Command(BaseCommand):
    help = 'Import receipts from an Excel file into the Receipt model'

    def handle(self, *args, **kwargs):
        error_html = "<html><head><title>Error Report</title></head><body>"

        try:
            # Endpoint de autenticación
            auth_url = 'http://localhost:8001/api/auth/login'
            # Credenciales para autenticarse
            auth_data = {
                'email': 'prod@yopmail.com',
                'password': 'smartevolution'
            }

            # Realizar la solicitud de autenticación
            try:
                auth_response = requests.post(auth_url, json=auth_data)
                auth_response.raise_for_status()  # Lanza una excepción si la autenticación falla
                token = auth_response.json().get('access')
                if not token:
                    error_message = f"No se pudo obtener el token de autenticación. Respuesta: {auth_response.json()}"
                    error_html += f"<p>{error_message}</p>"
                    self.stderr.write(self.style.ERROR(error_message))
                    return
            except requests.exceptions.RequestException as e:
                error_message = f"Error durante la autenticación: {e}"
                error_html += f"<p>{error_message}</p>"
                self.stderr.write(self.style.ERROR(error_message))
                return

            # Definir encabezados con el token de autenticación
            headers = {'Authorization': f'Bearer {token}'}

            file_path = os.path.join(settings.BASE_DIR, 'apps/administration/management/commands/add_receipt/file.xlsx')
            
            # Leer el archivo Excel utilizando pandas
            try:
                data = pd.read_excel(file_path)
            except Exception as e:
                error_message = f"Error leyendo el archivo Excel: {e}"
                error_html += f"<p>{error_message}</p>"
                self.stderr.write(self.style.ERROR(error_message))
                return
            
            # Iterar sobre las filas del DataFrame y crear instancias del modelo
            for _, row in data.iterrows():
                # Verificar campos requeridos
                if pd.isna(row['operation_id']) or pd.isna(row['typeReceipt_id']):
                    error_message = f"Campos requeridos faltantes en la fila: operation_id o typeReceipt_id"
                    error_html += f"<p>{error_message}</p>"
                    self.stderr.write(self.style.ERROR(error_message))
                    continue
                
                # Buscar la operación correspondiente
                try:
                    operation = PreOperation.objects.get(id=row['operation_id'])
                except PreOperation.DoesNotExist:
                    error_message = f"Operation with id {row['operation_id']} does not exist"
                    error_html += f"<p>{error_message}</p>"
                    self.stderr.write(self.style.ERROR(error_message))
                    continue
                
                # Crear los datos para la petición POST
                payload = {
                    "state": row['state'],
                    "created_at": row['created_at'].isoformat() if pd.notna(row['created_at']) else None,
                    "updated_at": row['updated_at'].isoformat() if pd.notna(row['updated_at']) else None,
                    "date": row['date'].strftime('%Y-%m-%d') if pd.notna(row['date']) else None,  # Corregido para el formato YYYY-MM-DD
                    "typeReceipt": row['typeReceipt_id'],
                    "payedAmount": row['payedAmount'],
                    "investorInterests": row['investorInterests'],
                    "tableInterests": row['tableInterests'],
                    "additionalDays": row['additionalDays'],
                    "operation": row['operation_id'],
                    "user_created_at": row['user_created_at_id'],
                    "user_updated_at": row['user_updated_at_id'],
                    "additionalInterests": row['additionalInterests'],
                    "additionalInterestsSM": row['additionalInterestsSM'],
                    "futureValueRecalculation": row['futureValueRecalculation'],
                    "tableRemaining": row['tableRemaining'],
                    "realDays": row['realDays'],
                    "account": row['account_id'],
                    "calculatedDays": row['calculatedDays'],
                    "remaining": row['remaining'],
                    "receiptStatus": row['receiptStatus_id'],
                    "presentValueInvestor": row['presentValueInvestor']
                }

                # Reemplazar NaN con None para ser JSON compatible
                payload = {k: (None if (isinstance(v, float) and math.isnan(v)) else v) for k, v in payload.items()}
                
                # Enviar la petición POST a la API con el token de autenticación
                try:
                    response = requests.post('http://localhost:8001/api/receipt/', json=payload, headers=headers)
                    response.raise_for_status()  # Esto lanzará una excepción si la petición no tuvo éxito
                    self.stdout.write(self.style.SUCCESS(f"Successfully sent receipt {row['id']} to API"))
                except requests.exceptions.HTTPError as e:
                    # Mostrar el error HTTP detallado
                    error_message = f"HTTP error occurred: {e}"
                    error_detail = f"Server response: {response.status_code} - {response.text}"
                    error_html += f"<p>{error_message}</p><p>{error_detail}</p>"
                    self.stderr.write(self.style.ERROR(error_message))
                    self.stderr.write(self.style.ERROR(error_detail))
                except requests.exceptions.RequestException as e:
                    # Mostrar cualquier otro error de RequestException
                    error_message = f"Error sending data to API for receipt {row['id']}: {e}"
                    error_html += f"<p>{error_message}</p>"
                    self.stderr.write(self.style.ERROR(error_message))

            self.stdout.write(self.style.SUCCESS("Finished processing all rows"))
        
        except Exception as e:
            # Capturar cualquier otro error no manejado
            error_message = f"Unexpected error: {e}"
            error_html += f"<p>{error_message}</p>"
            self.stderr.write(self.style.ERROR(error_message))
        
        finally:
            # Guardar errores en un archivo HTML
            error_html += "</body></html>"
            with open('error_report.html', 'w', encoding='utf-8') as f:
                f.write(error_html)
