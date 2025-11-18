import requests
from apps.base.exceptions import HttpException

def  billEvents(bill_data):
    try:
        if bill_data is None:
            return []
        
        # Extraer eventos de la nueva estructura de la API
        events_from_api = bill_data.get('data', {}).get('attributes', {}).get('events', [])
        
        # Mapeo de códigos API a UUID de TypeEvent
        event_code_to_uuid = {
            '036': 'b8d4f8d3-aded-4b1f-873e-46c89a2538ed',
            '037': '3ea77762-7208-457a-b035-70069ee42b5e',
            '038': '0e333b6b-27b1-4aaf-87ce-ad60af6e52e6',
            '046': 'f5d475c0-4433-422f-b3d2-7964ea0aa5c4'
        }
        
        parsed_events = []
        
        for api_event in events_from_api:
            event_code = api_event.get('code')
            
            # Solo procesar eventos específicos (036, 037, 038, 046)
            if event_code in event_code_to_uuid:
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
                
                # Agregar a los eventos parseados
                parsed_events.append({
                    'event': event_uuid,
                    'date': event_date,
                    'code': event_code
                })
        
        return parsed_events

    except Exception as e:
        print(f"Error en updateBillEvents: {str(e)}")
        return []