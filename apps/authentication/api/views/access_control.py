from django.db import transaction
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email
from django.db.models import Q
from django.shortcuts import get_object_or_404
from base64 import b64decode
from urllib.parse import urlparse
import json
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.base.utils.index import gen_uuid
from apps.base.utils.getContentInfo import get_content_info
from apps.base.utils.uploadBase64File import BucketS3
from apps.authentication.access import get_access_profile, permission_required, user_has_permission
from apps.authentication.models import User, Role, UserRole, Permission, RolePermission, AccessAudit
from apps.client.api.models.client.index import Client, ClientAccess
import secrets

USER_PROFILE_PHOTO_FOLDER = 'user-profiles'
ALLOWED_PROFILE_IMAGE_TYPES = {'png', 'jpg', 'jpeg', 'webp'}
MAX_PROFILE_IMAGE_SIZE = 5 * 1024 * 1024

def upload_user_profile_photo(user_id, data_url):
    if not data_url:
        return None
    if isinstance(data_url, str) and data_url.startswith('http'):
        return data_url
    if hasattr(data_url, 'read'):
        content_type = str(getattr(data_url, 'content_type', '')).lower()
        extension = content_type.split('/')[-1].replace('jpeg', 'jpg')
        file_bytes = data_url.read()
    else:
        try:
            file_content = get_content_info(data_url)
        except Exception as exc:
            raise serializers.ValidationError({'profile_photo': 'La foto de perfil no tiene un formato válido.'}) from exc
        extension = file_content['file_format'].lower()
        content_type = f"image/{'jpeg' if extension == 'jpg' else extension}"
        try:
            file_bytes = b64decode(file_content['content'], validate=True)
        except Exception as exc:
            raise serializers.ValidationError({'profile_photo': 'No fue posible leer la imagen enviada.'}) from exc
    if extension not in ALLOWED_PROFILE_IMAGE_TYPES:
        raise serializers.ValidationError({'profile_photo': 'La foto de perfil debe ser una imagen PNG, JPG, JPEG o WEBP.'})
    if len(file_bytes) > MAX_PROFILE_IMAGE_SIZE:
        raise serializers.ValidationError({'profile_photo': 'La foto de perfil no puede superar 5 MB.'})
    key = f'{USER_PROFILE_PHOTO_FOLDER}/{user_id}/{gen_uuid()}.{extension}'
    BucketS3().upload_file(file=file_bytes, file_path=key, content_type=content_type)
    return f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/{key}"


def delete_user_profile_photo(photo_url):
    if not photo_url:
        return
    parsed = urlparse(photo_url)
    key = parsed.path.lstrip('/')
    expected_host = f'{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
    if parsed.netloc != expected_host or not key.startswith(f'{USER_PROFILE_PHOTO_FOLDER}/'):
        return
    BucketS3().session.client('s3').delete_object(
        Bucket=settings.AWS_STORAGE_BUCKET_NAME,
        Key=key,
    )


def replace_user_profile_photo(user, value):
    previous = user.profile_photo
    uploaded = upload_user_profile_photo(user.id, value)
    if previous and previous != uploaded:
        delete_user_profile_photo(previous)
    return uploaded


def revoke_user_sessions(user):
    user.token_version += 1


def request_roles(data):
    roles = data.get('roles', [])
    if isinstance(roles, str):
        try:
            roles = json.loads(roles)
        except json.JSONDecodeError:
            roles = [roles]
    return roles if isinstance(roles, list) else []


def request_boolean(value):
    if isinstance(value, str):
        return value.lower() in ('true', '1', 'yes')
    return bool(value)


def user_can_be_purged(user):
    if user.is_active or not user.archived_at or user.is_staff or user.is_superuser:
        return False
    allowed_relations = {'userrole_set', 'auth_token'}
    for relation in user._meta.related_objects:
        accessor = relation.get_accessor_name()
        if accessor in allowed_relations:
            continue
        try:
            related = getattr(user, accessor)
        except relation.related_model.DoesNotExist:
            continue
        if hasattr(related, 'exists'):
            if related.exists():
                return False
        elif related is not None:
            return False
    return True


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
    role_details = serializers.SerializerMethodField()
    client_access = serializers.SerializerMethodField()
    company = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = (
            'id','first_name','last_name','email','phone_number','profile_photo',
            'organization','company','description','is_active','is_staff',
            'is_superuser','archived_at','last_login','date_joined','roles',
            'role_details','client_access','can_delete',
        )
    def get_roles(self, obj): return list(UserRole.objects.filter(user=obj,state=True).values_list('role__code',flat=True))
    def get_role_details(self, obj):
        return list(UserRole.objects.filter(user=obj,state=True).values('role__code','role__name'))
    def get_client_access(self, obj):
        access = getattr(obj,'client_access',None)
        return None if not access else {'id':access.id,'client_id':access.client_id,'status':access.status}
    def get_company(self, obj):
        if obj.organization:
            return obj.organization
        access = getattr(obj, 'client_access', None)
        if not access:
            return ''
        return access.client.social_reason or f'{access.client.first_name or ""} {access.client.last_name or ""}'.strip()
    def get_can_delete(self, obj):
        return user_can_be_purged(obj)

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

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id','first_name','last_name','email','phone_number','profile_photo','last_login','date_joined')
        read_only_fields = ('id','email','last_login','date_joined')

class ProfileAV(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        return Response({'error': False, 'data': ProfileSerializer(request.user).data})

    @transaction.atomic
    def patch(self, request):
        user = request.user
        update_fields = []
        for field in ('first_name', 'last_name', 'phone_number'):
            if field in request.data:
                setattr(user, field, request.data.get(field) or '')
                update_fields.append(field)
        if 'profile_photo' in request.data:
            user.profile_photo = replace_user_profile_photo(user, request.data.get('profile_photo'))
            update_fields.append('profile_photo')
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')
        if new_password or confirm_password or current_password:
            if not current_password or not user.check_password(current_password):
                return Response({'error': True, 'message': 'La contraseña actual no es correcta.'}, status=400)
            if new_password != confirm_password:
                return Response({'error': True, 'message': 'Las contraseñas no coinciden.'}, status=400)
            try:
                validate_password(new_password, user=user)
            except DjangoValidationError as exc:
                return Response({'error': True, 'message': list(exc.messages)}, status=400)
            user.set_password(new_password)
            revoke_user_sessions(user)
            update_fields.extend(['password', 'token_version'])
        if update_fields:
            user.save(update_fields=list(dict.fromkeys(update_fields)))
        return Response({'error': False, 'data': ProfileSerializer(user).data})

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
    def get(self,request):
        users = User.objects.select_related('client_access__client').all().order_by('email')
        return Response({'error':False,'data':UserAdminSerializer(users,many=True).data})
    @permission_required('users.create')
    @transaction.atomic
    def post(self,request):
        email = str(request.data.get('email') or '').strip().lower()
        try:
            validate_email(email)
        except DjangoValidationError:
            return Response({'error':True,'message':'Ingresa un correo electrónico válido.'},status=400)
        if User.objects.filter(email__iexact=email).exists():
            return Response({'error':True,'message':'El correo ya está registrado.'},status=400)
        temporary_password=request.data.get('password') or secrets.token_urlsafe(10)
        first_name = str(request.data.get('first_name') or '').strip()
        last_name = str(request.data.get('last_name') or '').strip()
        roles = request_roles(request.data)
        if not first_name or not last_name or not roles:
            return Response({'error':True,'message':'Nombres, apellidos y rol son obligatorios.'},status=400)
        if Role.objects.filter(code__in=roles,state=True).count() != len(set(roles)):
            return Response({'error':True,'message':'Uno o más roles seleccionados no están disponibles.'},status=400)
        description = str(request.data.get('description') or '')
        if len(description) > 1000:
            return Response({'error':True,'message':'Las notas internas no pueden superar 1.000 caracteres.'},status=400)
        user=User(
            id=gen_uuid(), email=email,
            first_name=first_name, last_name=last_name,
            phone_number=request.data.get('phone_number') or None,
            organization=request.data.get('organization') or None,
            description=description or None, is_active=True,
        )
        user.set_password(temporary_password); user.save()
        profile_photo = upload_user_profile_photo(user.id, request.data.get('profile_photo'))
        if profile_photo:
            user.profile_photo = profile_photo
            user.save(update_fields=['profile_photo'])
        for role in Role.objects.filter(code__in=roles,state=True):
            UserRole.objects.create(id=gen_uuid(),user=user,role=role,user_created_at=request.user)
        audit(request,'USER_CREATED','user',user.id,{'email':user.email,'roles':roles})
        return Response({'error':False,'data':UserAdminSerializer(user).data,'temporary_password':temporary_password},status=201)


class UserMetricsAV(APIView):
    permission_classes = [IsAuthenticated]

    @permission_required('users.view')
    def get(self, request):
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        blocked_users = total_users - active_users
        client_accounts = ClientAccess.objects.filter(state=True).count()
        associated_client_accounts = ClientAccess.objects.filter(
            state=True,
            user__isnull=False,
        ).count()

        def percentage(value, total):
            return round((value / total) * 100, 1) if total else 0

        return Response({
            'error': False,
            'data': {
                'total_users': total_users,
                'active_users': active_users,
                'active_percentage': percentage(active_users, total_users),
                'client_accounts': client_accounts,
                'associated_client_accounts': associated_client_accounts,
                'client_association_percentage': percentage(
                    associated_client_accounts,
                    client_accounts,
                ),
                'blocked_users': blocked_users,
                'blocked_percentage': percentage(blocked_users, total_users),
            },
        })


class UserAdminDetailAV(APIView):
    permission_classes=[IsAuthenticated]
    @permission_required('users.view')
    def get(self,request,pk):
        user = get_object_or_404(User.objects.select_related('client_access__client'), pk=pk)
        return Response({'error':False,'data':UserAdminSerializer(user).data})

    @transaction.atomic
    def patch(self,request,pk):
        required='users.assign_roles' if 'roles' in request.data else ('users.block' if 'is_active' in request.data else 'users.update')
        if not user_has_permission(request.user,required): return Response({'error':True,'message':'No tiene permiso para este cambio de usuario.'},status=403)
        user=get_object_or_404(User,pk=pk)
        if user == request.user and request.data.get('is_active') is False:
            return Response({'error':True,'message':'No puede bloquear su propia cuenta.'},status=400)
        update_fields = []
        if 'is_active' in request.data:
            user.is_active=request_boolean(request.data['is_active'])
            update_fields.append('is_active')
            if not user.is_active:
                revoke_user_sessions(user)
                update_fields.append('token_version')
        for field in ('first_name','last_name','phone_number','organization','description'):
            if field in request.data:
                setattr(user, field, request.data.get(field) or '')
                update_fields.append(field)
        if len(user.description or '') > 1000:
            return Response({'error':True,'message':'Las notas internas no pueden superar 1.000 caracteres.'},status=400)
        if 'email' in request.data:
            email = str(request.data.get('email') or '').strip().lower()
            try:
                validate_email(email)
            except DjangoValidationError:
                return Response({'error':True,'message':'Ingresa un correo electrónico válido.'},status=400)
            if User.objects.filter(email__iexact=email).exclude(pk=user.pk).exists():
                return Response({'error':True,'message':'El correo ya está registrado.'},status=400)
            user.email = email
            update_fields.append('email')
        if 'profile_photo' in request.data:
            user.profile_photo = replace_user_profile_photo(user, request.data.get('profile_photo'))
            update_fields.append('profile_photo')
        if update_fields: user.save(update_fields=update_fields)
        if 'roles' in request.data:
            roles = request_roles(request.data)
            if not roles:
                return Response({'error':True,'message':'El usuario debe tener al menos un rol.'},status=400)
            if Role.objects.filter(code__in=roles,state=True).count() != len(set(roles)):
                return Response({'error':True,'message':'Uno o más roles seleccionados no están disponibles.'},status=400)
            UserRole.objects.filter(user=user).delete()
            for role in Role.objects.filter(code__in=roles,state=True):
                UserRole.objects.create(id=gen_uuid(),user=user,role=role,user_created_at=request.user)
        audit(request,'USER_UPDATED','user',user.id,{'is_active':user.is_active,'roles':request_roles(request.data) if 'roles' in request.data else None})
        return Response({'error':False,'data':UserAdminSerializer(user).data})

    @permission_required('users.update')
    @transaction.atomic
    def delete(self,request,pk):
        user=get_object_or_404(User,pk=pk)
        if user == request.user or user.is_staff or user.is_superuser:
            return Response({'error':True,'message':'Esta cuenta no puede eliminarse permanentemente.'},status=400)
        if user.is_active or not user.archived_at:
            return Response({'error':True,'message':'El usuario debe estar archivado antes de eliminarse.'},status=400)
        if not user_can_be_purged(user):
            return Response({'error':True,'message':'El usuario tiene trazabilidad histórica y no puede eliminarse.'},status=400)
        email = user.email
        delete_user_profile_photo(user.profile_photo)
        UserRole.objects.filter(user=user).delete()
        user.delete()
        audit(request,'USER_DELETED','user',pk,{'email':email})
        return Response({'error':False,'message':'Usuario eliminado permanentemente.'})


class UserPasswordAV(APIView):
    permission_classes=[IsAuthenticated]
    @permission_required('users.update')
    @transaction.atomic
    def post(self,request,pk):
        user=get_object_or_404(User,pk=pk)
        new_password=request.data.get('new_password') or ''
        confirm_password=request.data.get('confirm_password') or ''
        if new_password != confirm_password:
            return Response({'error':True,'message':'Las contraseñas no coinciden.'},status=400)
        if len(new_password) < 8 or not any(c.isupper() for c in new_password) or not any(c.isdigit() for c in new_password):
            return Response({'error':True,'message':'La contraseña debe tener mínimo 8 caracteres, una mayúscula y un número.'},status=400)
        try:
            validate_password(new_password,user=user)
        except DjangoValidationError as exc:
            return Response({'error':True,'message':list(exc.messages)},status=400)
        user.set_password(new_password)
        revoke_user_sessions(user)
        user.save(update_fields=['password','token_version'])
        audit(request,'USER_PASSWORD_CHANGED','user',user.id)
        return Response({'error':False,'message':'Contraseña actualizada y sesiones cerradas.'})


class UserArchiveAV(APIView):
    permission_classes=[IsAuthenticated]
    @permission_required('users.block')
    @transaction.atomic
    def post(self,request,pk):
        user=get_object_or_404(User,pk=pk)
        if user == request.user:
            return Response({'error':True,'message':'No puede archivar su propia cuenta.'},status=400)
        user.is_active=False
        user.archived_at=timezone.now()
        revoke_user_sessions(user)
        user.save(update_fields=['is_active','archived_at','token_version'])
        audit(request,'USER_ARCHIVED','user',user.id,{'email':user.email})
        return Response({'error':False,'data':UserAdminSerializer(user).data})


class UserRestoreAV(APIView):
    permission_classes=[IsAuthenticated]
    @permission_required('users.block')
    @transaction.atomic
    def post(self,request,pk):
        user=get_object_or_404(User,pk=pk)
        user.is_active=True
        user.archived_at=None
        user.save(update_fields=['is_active','archived_at'])
        audit(request,'USER_RESTORED','user',user.id,{'email':user.email})
        return Response({'error':False,'data':UserAdminSerializer(user).data})


class UserOperationsAV(APIView):
    permission_classes=[IsAuthenticated]
    @permission_required('users.view')
    def get(self,request,pk):
        get_object_or_404(User,pk=pk)
        from apps.operation.api.models.preOperation.index import PreOperation
        filter_name=request.query_params.get('status','pending')
        page=max(int(request.query_params.get('page',1)),1)
        page_size=min(max(int(request.query_params.get('page_size',5)),1),50)
        queryset=PreOperation.objects.filter(user_created_at_id=pk).select_related('emitter').order_by('-opDate','-opId')
        queryset=queryset.filter(status=1) if filter_name == 'approved' else queryset.exclude(status=1)
        total=queryset.count()
        start=(page-1)*page_size
        rows=[]
        for operation in queryset[start:start+page_size]:
            rows.append({
                'id':operation.id,
                'operation_id':operation.opId,
                'date':operation.opDate,
                'emitter':operation.emitter.social_reason or f'{operation.emitter.first_name or ""} {operation.emitter.last_name or ""}'.strip(),
                'nominal_value':operation.amount,
                'status':'Aprobada' if operation.status == 1 else 'Por aprobar',
            })
        pending=PreOperation.objects.filter(user_created_at_id=pk).exclude(status=1).count()
        approved=PreOperation.objects.filter(user_created_at_id=pk,status=1).count()
        return Response({'error':False,'data':{'results':rows,'total':total,'page':page,'page_size':page_size,'counts':{'pending':pending,'approved':approved}}})

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
