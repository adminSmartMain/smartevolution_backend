# REST Framework imports
from rest_framework.decorators import APIView
# Models
from apps.misc.models import Department
# Serializers
from apps.misc.api.serializers.index import DepartmentSerializer
# Utils
from apps.base.utils.index import response, gen_uuid
# Decorators
from apps.base.decorators.index import checkRole


class DepartmentAV(APIView):
    
        def get(self, request, pk=None):
            try:
                if pk:
                    department = Department.objects.get(pk=pk)
                    serializer = DepartmentSerializer(department)
                    return response({'error': False, 'data': serializer.data}, 200)
                else:
                    department = Department.objects.filter(state=1).order_by('description')
                    serializer = DepartmentSerializer(department, many=True)
                    return response({'error': False, 'data': serializer.data}, 200)
            except Department.DoesNotExist:
                return response({'error': True, 'message': 'departamento no encontrado'}, 404)
            except Exception as e:
                return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
    
        @checkRole(['superuser'])
        def post(self, request):
            try:
                request.data['id'] = gen_uuid()
                serializer = DepartmentSerializer(data=request.data, context={'request':request})
                if serializer.is_valid():
                    serializer.save()
                    return response({'error': False, 'message': 'departamento creado', 'data':serializer.data}, 200)
                return response({'error': True, 'message': serializer.errors}, 400)
            except Exception as e:
                return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
    
        @checkRole(['superuser'])
        def patch(self, request, pk):
            try:
                department = Department.objects.get(pk=pk)
                serializer = DepartmentSerializer(department, data=request.data, context={'request':request})
                if serializer.is_valid():
                    serializer.save()
                    return response({'error': False, 'message': 'departamento actualizado', 'data': serializer.data}, 200)
                return response({'error': True, 'message': serializer.errors}, 400)
            except Department.DoesNotExist:
                return response({'error': True, 'message': 'departamento no encontrado'}, 404)
            except Exception as e:
                return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
        
        @checkRole(['superuser'])
        def delete(self, request, pk):
            try:
                department = Department.objects.get(pk=pk)
                department.state = 0
                department.save()
                return response({'error': False, 'message': 'departamento eliminado'}, 204)
            except Department.DoesNotExist:
                return response({'error': True, 'message': 'departamento no encontrado'}, 404)
            except Exception as e:
                return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)