# REST Framework imports
from http import client
from rest_framework.decorators import APIView
# Models
from apps.client.models import Contact
# Serializers
from apps.client.api.serializers.index import ContactSerializer
# Utils
from apps.base.utils.index import response
# Decorators
from apps.base.decorators.index import checkRole

class ContactAV(APIView):
    @checkRole('admin')
    def get(self, request, pk=None):
        try:
            if pk:
                contact    = Contact.objects.filter(client=pk)
                serializer = ContactSerializer(contact, many=True)
                return response({'error': False, 'data': serializer.data}, 200)
            else:
                contacts   = Contact.objects.filter(state=1)
                serializer = ContactSerializer(contacts, many=True)
                return response({'error': False, 'data': serializer.data}, 200)
        except Contact.DoesNotExist:
            return response({'error': True, 'message': 'contactos no encontrados'}, 404)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
    
    @checkRole('admin')
    def post(self, request):
        try:
            serializer = ContactSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return response({'error': False, 'data': serializer.data}, 200)
            else:
                return response({'error': True, 'message': serializer.errors}, 400)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
    
    @checkRole('admin')
    def patch(self, request, pk=None):
        try:
            contact    = Contact.objects.get(pk=pk)
            serializer = ContactSerializer(contact, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return response({'error': False, 'data': serializer.data}, 200)
            else:
                return response({'error': True, 'message': serializer.errors}, 400)
        except Contact.DoesNotExist:
            return response({'error': True, 'message': 'Contacto no encontrado'}, 404)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)
    
    @checkRole('admin')
    def delete(self, request, pk=None):
        try:
            contact = Contact.objects.get(pk=pk)
            contact.state = 0
            contact.save()
            return response({'error': False, 'message': 'Contacto eliminado'}, 200)
        except Contact.DoesNotExist:
            return response({'error': True, 'message': 'Contacto no encontrado'}, 404)
        except Exception as e:
            return response({'error': True, 'message': str(e)}, e.status_code if hasattr(e, 'status_code') else 500)

