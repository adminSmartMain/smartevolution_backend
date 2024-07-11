# REST Framework imports
from rest_framework.decorators import APIView
# Models
from apps.authentication.api.models.index import User
# Serializers
from apps.authentication.api.serializers.index import UserReadOnlySerializer, UpdateUserSerializer, UserRoleSerializer
# Utils
from apps.base.utils.index import response, sendEmail
# Decorators
from apps.base.decorators.index import checkRole


class UserAV(APIView):
    @checkRole(['admin'])
    def get(self, request, pk=None):
        try:
            if pk:
                user       = User.objects.get(pk=pk)
                serializer = UserReadOnlySerializer(user)
                return response({'error':False, 'data': serializer.data},200)
            else:
                users      = User.objects.all()
                serializer = UserReadOnlySerializer(users, many=True)
                return response({'error':False, 'data': serializer.data},200)
        except User.DoesNotExist:
            return response({'error':True, 'message': 'user not found'}, 404)
        except Exception as e:
            return response({'error':True, 'message': str(e)}, 500)
    
    @checkRole(['admin'])
    def patch(self, request, pk=None):
        try:
            if pk:
                user       = User.objects.get(pk=pk)
                serializer = UpdateUserSerializer(user, data=request.data, context={'request': request})
                if serializer.is_valid():
                    serializer.save()
                    return response({'error':False, 'data': serializer.data},200)
                return response({'error':True, 'message': serializer.errors}, 400)
            else:
                return response({'error':True, 'message': 'id not provided'}, 404)
        except User.DoesNotExist:
            return response({'error':True, 'message': 'user not found'}, 404)
        except Exception as e:
            return response({'error':True, 'message': str(e)}, 500)

    @checkRole(['admin'])
    def delete(self, request, pk=None):
        try:
            if pk:
                user = User.objects.get(pk=pk)
                user.status = 0
                user.save()
                return response({'error':False, 'message': 'user deleted'},200)
            else:
                return response({'error':True, 'message': 'id not provided'}, 404)
        except User.DoesNotExist:
            return response({'error':True, 'message': 'user not found'}, 404)
        except Exception as e:
            return response({'error':True, 'message': str(e)}, 500)


class UserRolesAV(APIView):
    @checkRole(['admin'])
    def get(self, request, pk=None):
        try:
            if pk:
                roleList = []
                userRoles = UserRoleSerializer.Meta.model.objects.filter(user=pk)
                for role in userRoles:
                    roleList.append(role.role.description)
                return response({'error':False, 'data': roleList},200)
            else:
                return response({'error': True, 'message': 'id not provided'}, 400)
        except User.DoesNotExist:
            return response({'error':True, 'message': 'user not found'}, 404)
        except Exception as e:
            return response({'error':True, 'message': str(e)}, 500)
