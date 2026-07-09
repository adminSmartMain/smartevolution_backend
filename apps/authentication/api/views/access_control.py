from django.db import transaction
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.base.utils.index import gen_uuid
from apps.authentication.access import get_access_profile, permission_required, user_has_permission
from apps.authentication.models import User, Role, UserRole, Permission, RolePermission, AccessAudit
from apps.client.api.models.client.index import Client, ClientAccess
import secrets

def audit(request, action, target_type, target_id=None, details=None):
    AccessAudit.objects.create(id=gen_uuid(),actor=request.user,action=action,target_type=target_type,target_id=str(target_id) if target_id else None,details=details or {},ip_address=request.META.get('REMOTE_ADDR'))


class PermissionSerializer(serializers.ModelSerializer):
    class Meta: model = Permission; fields = ('id','code','module','action','name','description','state')

class RoleAdminSerializer(serializers.ModelSerializer):
    permissions = serializers.SerializerMethodField()
    class Meta: model = Role; fields = ('id','code','name','description','audience','is_system','state','permissions')
    def get_permissions(self, obj):
        return list(obj.permission_assignments.filter(state=True, permission__state=True).values_list('permission__code', flat=True))

class UserAdminSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()
    client_access = serializers.SerializerMethodField()
    class Meta: model = User; fields = ('id','first_name','last_name','email','phone_number','is_active','is_staff','is_superuser','last_login','date_joined','roles','client_access')
    def get_roles(self, obj): return list(UserRole.objects.filter(user=obj,state=True).values_list('role__code',flat=True))
    def get_client_access(self, obj):
        access = getattr(obj,'client_access',None)
        return None if not access else {'id':access.id,'client_id':access.client_id,'status':access.status}

class ClientAccessSerializer(serializers.ModelSerializer):
    client_name = serializers.SerializerMethodField()
    user_email = serializers.CharField(source='user.email', read_only=True)
    class Meta: model = ClientAccess; fields = ('id','client','client_name','user','user_email','status','activated_at','blocked_at','blocked_reason','state')
    def get_client_name(self,obj): return obj.client.social_reason or f'{obj.client.first_name or ""} {obj.client.last_name or ""}'.strip()

class AccessAuditSerializer(serializers.ModelSerializer):
    actor_email=serializers.CharField(source='actor.email',read_only=True)
    class Meta: model=AccessAudit; fields=('id','actor_email','action','target_type','target_id','details','ip_address','created_at')

class MeAV(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        return Response({'error':False,'data':get_access_profile(request.user)})

class PermissionListAV(APIView):
    permission_classes = [IsAuthenticated]
    @permission_required('permissions.view')
    def get(self, request): return Response({'error':False,'data':PermissionSerializer(Permission.objects.all(),many=True).data})

class RoleListAV(APIView):
    permission_classes = [IsAuthenticated]
    @permission_required('roles.view')
    def get(self, request): return Response({'error':False,'data':RoleAdminSerializer(Role.objects.prefetch_related('permission_assignments__permission'),many=True).data})
    @permission_required('roles.create')
    def post(self, request):
        data=request.data
        role=Role.objects.create(id=gen_uuid(),code=data['code'].upper(),name=data['name'],description=data.get('description',''),audience=data.get('audience','INTERNAL'),state=True,user_created_at=request.user)
        self._set_permissions(role,data.get('permissions',[]),request.user)
        audit(request,'ROLE_CREATED','role',role.id,{'code':role.code,'permissions':data.get('permissions',[])})
        return Response({'error':False,'data':RoleAdminSerializer(role).data},status=201)
    def _set_permissions(self,role,codes,user):
        RolePermission.objects.filter(role=role).delete()
        for permission in Permission.objects.filter(code__in=codes,state=True):
            RolePermission.objects.create(id=gen_uuid(),role=role,permission=permission,user_created_at=user)

class RoleDetailAV(RoleListAV):
    def patch(self,request,pk):
        if not user_has_permission(request.user,'roles.update'): return Response({'error':True,'message':'No puede editar roles.'},status=403)
        role=Role.objects.get(pk=pk)
        if role.is_system and not request.user.is_superuser: return Response({'error':True,'message':'Los roles del sistema solo pueden ser modificados por un superusuario.'},status=403)
        for field in ('name','description','audience','state'):
            if field in request.data: setattr(role,field,request.data[field])
        role.updated_at=timezone.now(); role.user_updated_at=request.user; role.save()
        if 'permissions' in request.data:
            if not user_has_permission(request.user,'roles.assign_permissions'): return Response({'error':True,'message':'No puede asignar permisos.'},status=403)
            self._set_permissions(role,request.data['permissions'],request.user)
        audit(request,'ROLE_UPDATED','role',role.id,{'code':role.code,'permissions':request.data.get('permissions')})
        return Response({'error':False,'data':RoleAdminSerializer(role).data})
    @permission_required('roles.delete')
    def delete(self,request,pk):
        role=Role.objects.get(pk=pk)
        if role.is_system: return Response({'error':True,'message':'Un rol del sistema no puede eliminarse.'},status=400)
        if UserRole.objects.filter(role=role,state=True).exists(): return Response({'error':True,'message':'El rol tiene usuarios asignados; reasígnelos antes de desactivarlo.'},status=400)
        role.state=False; role.updated_at=timezone.now(); role.user_updated_at=request.user; role.save()
        audit(request,'ROLE_DISABLED','role',role.id,{'code':role.code})
        return Response({'error':False,'message':'Rol desactivado.'})

class UserAdminAV(APIView):
    permission_classes=[IsAuthenticated]
    @permission_required('users.view')
    def get(self,request): return Response({'error':False,'data':UserAdminSerializer(User.objects.all().order_by('email'),many=True).data})
    @permission_required('users.create')
    @transaction.atomic
    def post(self,request):
        if User.objects.filter(email__iexact=request.data['email']).exists():
            return Response({'error':True,'message':'El correo ya está registrado.'},status=400)
        temporary_password=request.data.get('password') or secrets.token_urlsafe(10)
        user=User(id=gen_uuid(),email=request.data['email'].lower(),first_name=request.data.get('first_name',''),last_name=request.data.get('last_name',''),is_active=True)
        user.set_password(temporary_password); user.save()
        for role in Role.objects.filter(code__in=request.data.get('roles',[]),state=True):
            UserRole.objects.create(id=gen_uuid(),user=user,role=role,user_created_at=request.user)
        audit(request,'USER_CREATED','user',user.id,{'email':user.email,'roles':request.data.get('roles',[])})
        return Response({'error':False,'data':UserAdminSerializer(user).data,'temporary_password':temporary_password},status=201)

class UserAdminDetailAV(APIView):
    permission_classes=[IsAuthenticated]
    @transaction.atomic
    def patch(self,request,pk):
        required='users.assign_roles' if 'roles' in request.data else ('users.block' if 'is_active' in request.data else 'users.update')
        if not user_has_permission(request.user,required): return Response({'error':True,'message':'No tiene permiso para este cambio de usuario.'},status=403)
        user=User.objects.get(pk=pk)
        if user == request.user and request.data.get('is_active') is False:
            return Response({'error':True,'message':'No puede bloquear su propia cuenta.'},status=400)
        if 'is_active' in request.data: user.is_active=request.data['is_active']; user.save(update_fields=['is_active'])
        if 'roles' in request.data:
            UserRole.objects.filter(user=user).delete()
            for role in Role.objects.filter(code__in=request.data['roles'],state=True):
                UserRole.objects.create(id=gen_uuid(),user=user,role=role,user_created_at=request.user)
        audit(request,'USER_UPDATED','user',user.id,{'is_active':user.is_active,'roles':request.data.get('roles')})
        return Response({'error':False,'data':UserAdminSerializer(user).data})

class ClientAccessAV(APIView):
    permission_classes=[IsAuthenticated]
    @permission_required('client_access.view')
    def get(self,request): return Response({'error':False,'data':ClientAccessSerializer(ClientAccess.objects.select_related('client','user'),many=True).data})
    @permission_required('client_access.create')
    @transaction.atomic
    def post(self,request):
        client=Client.objects.get(pk=request.data['client'])
        temporary_password=None
        if request.data.get('user'):
            user=User.objects.get(pk=request.data['user'])
        else:
            if not client.email: return Response({'error':True,'message':'El cliente no tiene correo para crear su cuenta.'},status=400)
            if User.objects.filter(email__iexact=client.email).exists(): return Response({'error':True,'message':'Ya existe un usuario con el correo del cliente; selecciónelo en lugar de crear otro.'},status=400)
            temporary_password=secrets.token_urlsafe(10)
            user=User(id=gen_uuid(),email=client.email.lower(),first_name=client.first_name or client.social_reason or '',last_name=client.last_name or '',is_active=True)
            user.set_password(temporary_password); user.save()
        access=ClientAccess.objects.create(id=gen_uuid(),client=client,user=user,status=request.data.get('status','ACTIVE'),activated_at=timezone.now(),user_created_at=request.user)
        client_role=Role.objects.filter(code='CLIENT_USER').first()
        if client_role: UserRole.objects.get_or_create(user=user,role=client_role,defaults={'id':gen_uuid(),'user_created_at':request.user})
        audit(request,'CLIENT_ACCESS_CREATED','client_access',access.id,{'client_id':client.id,'user_id':user.id})
        return Response({'error':False,'data':ClientAccessSerializer(access).data,'temporary_password':temporary_password},status=201)

class ClientAccessOptionsAV(APIView):
    permission_classes=[IsAuthenticated]
    @permission_required('client_access.create')
    def get(self,request):
        clients=Client.objects.filter(state=True).exclude(access_account__isnull=False).prefetch_related('role_assignments__role').order_by('social_reason','first_name')
        client_data=[]
        for client in clients:
            name=client.social_reason or f'{client.first_name or ""} {client.last_name or ""}'.strip()
            client_data.append({'id':client.id,'name':name,'document_number':client.document_number,'email':client.email,'roles':list(client.role_assignments.filter(state=True).values_list('role__code',flat=True))})
        users=User.objects.filter(is_active=True,client_access__isnull=True).order_by('email').values('id','email','first_name','last_name')
        role_data=list(Role.objects.filter(state=True).values('code','name','audience','is_system','state'))
        return Response({'error':False,'data':{'clients':client_data,'users':list(users),'roles':role_data}})

class ClientAccessDetailAV(APIView):
    permission_classes=[IsAuthenticated]
    def patch(self,request,pk):
        required='client_access.block' if request.data.get('status') in ('BLOCKED','DISABLED') else 'client_access.update'
        if not user_has_permission(request.user,required): return Response({'error':True,'message':'No tiene permiso para modificar esta cuenta.'},status=403)
        access=ClientAccess.objects.get(pk=pk)
        new_status=request.data.get('status',access.status)
        access.status=new_status; access.blocked_reason=request.data.get('blocked_reason',access.blocked_reason)
        access.blocked_at=timezone.now() if new_status=='BLOCKED' else None
        access.user.is_active=new_status in ('ACTIVE','PENDING'); access.user.save(update_fields=['is_active'])
        access.updated_at=timezone.now(); access.user_updated_at=request.user; access.save()
        audit(request,'CLIENT_ACCESS_UPDATED','client_access',access.id,{'status':new_status,'reason':access.blocked_reason})
        return Response({'error':False,'data':ClientAccessSerializer(access).data})

class AccessAuditAV(APIView):
    permission_classes=[IsAuthenticated]
    @permission_required('audit.view')
    def get(self,request):
        rows=AccessAudit.objects.select_related('actor').all()[:500]
        return Response({'error':False,'data':AccessAuditSerializer(rows,many=True).data})
