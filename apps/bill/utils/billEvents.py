import requests
from apps.base.exceptions import HttpException
from apps.bill.api.models.bill.index import Bill
from apps.bill.api.models.event.index import BillEvent
from apps.misc.api.models.typeEvent.index import TypeEvent
from apps.base.utils.index import gen_uuid
import logging

# Configurar el logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Crear un handler de consola y definir el nivel
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# Crear un formato para los mensajes de log
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

# Añadir el handler al logger
logger.addHandler(console_handler)

def billEvents(cufe, update=False):
    try:
        # Tu token de autenticación para la API de Billy
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpaWQiOiItTkJ0MnktbG8yaENyeFNEUFdZOSIsInNjcCI6eyJpbnYiOjB9LCJpYXQiOjE3NjI3ODQxODAsImV4cCI6MTc5NDMyMDE4MCwic3ViIjoiR0JXdWZHcWZSc1ZFNUp3ZmxiTXdtNTVKeWZIMyIsImp0aSI6Ii1PZGk2emJ3YjFSZU1hQ05oSlNSIn0.Io2W8NumwKrTosCq9S_RnzqyMYX8IOJF89VhAiihhts"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Hacer la petición a la API de Billy
        response = requests.get(
            f"https://api.billy.com.co/v2/invoices?cufe={cufe}",
            headers=headers
        )
        
        # Verificar si la respuesta fue exitosa
        if response.status_code != 200:
            logger.error(f"Error en la API: {response.status_code} - {response.text}")
            return {
                "type": 'fdb5feb4-24e9-41fc-9689-31aff60b76c9', 
                "events": [], 
                'currentOwner': "", 
                'bill': None
            }
        
        data = response.json()

        
        # Extraer datos de la respuesta API
        data_attributes = data.get('data', {}).get('attributes', {})
        events_from_api = data_attributes.get('events', [])
        
        # Obtener currentOwner desde la API
        current_owner = data_attributes.get('holderName', '')
        
        # Mapeo de códigos API a UUID de TypeEvent
        event_code_to_uuid = {
            '030': '07c61f28-83f8-4f91-b965-f685f86cf6bf',
            '032': '141db270-23ec-49c1-87a7-352d5413d309',
            '033': 'c508eeb3-e0e8-48e8-a26f-5295f95c1f1f',
            '034': 'e76e9b7a-baeb-4972-b76e-3a8ce2d4fa30',
            '036': 'b8d4f8d3-aded-4b1f-873e-46c89a2538ed',
            '037': '3ea77762-7208-457a-b035-70069ee42b5e',
            '038': '0e333b6b-27b1-4aaf-87ce-ad60af6e52e6',
            '046': 'f5d475c0-4433-422f-b3d2-7964ea0aa5c4'
        }
        
        # Procesar eventos desde la API
        parsed_events = []
        valid = False
        
        for api_event in events_from_api:
            event_code = api_event.get('code')
            
            # Solo procesar eventos válidos que están en el mapeo
            if event_code in event_code_to_uuid:
                # Verificar si es un evento que marca como válido
                if event_code in ['030', '032', '033']:
                    valid = True
                
                # Para eventos de update, solo incluir si update=True
                if event_code in ['036', '037', '038', '046'] and not update:
                    continue
                    
                event_uuid = event_code_to_uuid[event_code]
                
                # Buscar la fecha en los detalles
                event_date = ""
                details = api_event.get('details', [])
                if details:
                    first_detail = details[0]
                    if 'timestamp' in first_detail:
                        # Convertir timestamp a fecha (formato YYYY-MM-DD)
                        from datetime import datetime
                        timestamp = first_detail['timestamp']
                        event_date = datetime.fromtimestamp(timestamp / 1000).strftime('%Y-%m-%d')
                
                # Solo crear eventos parseados sin guardar en BD (porque la factura no existe aún)
                parsed_events.append({
                    'event': event_uuid,
                    'description': first_detail.get('description', '') if details else '',
                    'date': event_date
                })
        

        
        # Determinar el tipo de respuesta
        response_type = 'a7c70741-8c1a-4485-8ed4-5297e54a978a' if valid else 'fdb5feb4-24e9-41fc-9689-31aff60b76c9'
        data1={
            "type": response_type,
            "events": parsed_events, 
            'currentOwner': current_owner,
            'bill': data
        }
        logger.debug(data1)
        return {
            "type": response_type,
            "events": parsed_events, 
            'currentOwner': current_owner,
            'bill': data
        }
        
    except Exception as e:
        logger.error(f"Error en billEvents: {str(e)}")
        raise HttpException(str(e))