# REST Framework imports
from rest_framework.decorators import APIView
# Models
from apps.misc.models import TypeCLient
# Utils
from apps.base.utils.index import response


class TestAV(APIView):
    
        def post(self, request):
            try:
                return response({'error': False, 'data':request.data['data']}, 200)
            except TypeCLient.DoesNotExist:
                return response({'error': True, 'message': 'tipo de cliente no encontrado'}, 404)
            except Exception as e:
                return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)