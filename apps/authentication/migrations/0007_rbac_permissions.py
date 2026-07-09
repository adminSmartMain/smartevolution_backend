import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


PERMISSIONS = [
    ('dashboard.view', 'dashboard', 'view', 'Ver panel'),
    ('clients.view', 'clients', 'view', 'Ver clientes'), ('clients.create', 'clients', 'create', 'Crear clientes'),
    ('clients.update', 'clients', 'update', 'Editar clientes'), ('clients.assign_roles', 'clients', 'assign_roles', 'Clasificar clientes'),
    ('operations.view', 'operations', 'view', 'Ver operaciones'), ('operations.create', 'operations', 'create', 'Crear operaciones'),
    ('operations.approve', 'operations', 'approve', 'Aprobar operaciones'),
    ('receipts.view', 'receipts', 'view', 'Ver recaudos'), ('receipts.create', 'receipts', 'create', 'Crear recaudos'),
    ('receipts.void', 'receipts', 'void', 'Anular recaudos'),
    ('accounting.view', 'accounting', 'view', 'Ver administración contable'),
    ('accounting.manage', 'accounting', 'manage', 'Gestionar administración contable'),
    ('users.view', 'users', 'view', 'Ver usuarios'), ('users.manage', 'users', 'manage', 'Gestionar usuarios'),
    ('roles.manage', 'roles', 'manage', 'Gestionar roles y permisos'),
    ('client_portal.access', 'client_portal', 'access', 'Acceder al portal de clientes'),
]


def seed_rbac(apps, schema_editor):
    Role, Permission, RolePermission, UserRole = (apps.get_model('authentication', n) for n in ('Role','Permission','RolePermission','UserRole'))
    UserRole.objects.values('user_id', 'role_id').annotate(n=models.Count('id')).filter(n__gt=1).iterator()
    seen = set()
    for item in UserRole.objects.order_by('created_at'):
        key = (item.user_id, item.role_id)
        if key in seen: item.delete()
        else: seen.add(key)
    for role in Role.objects.all():
        base = (role.description or 'ROLE').strip()
        code = ''.join(c if c.isalnum() else '_' for c in base.upper()).strip('_') or 'ROLE'
        candidate, i = code, 2
        while Role.objects.exclude(pk=role.pk).filter(code=candidate).exists():
            candidate, i = f'{code}_{i}', i + 1
        role.code, role.name = candidate, (role.name or base)
        role.save(update_fields=['code','name'])
    for code, module, action, name in PERMISSIONS:
        Permission.objects.get_or_create(code=code, defaults={'id':str(uuid.uuid4()),'module':module,'action':action,'name':name,'state':True})
    admin_permissions = list(Permission.objects.exclude(code='client_portal.access'))
    for role in Role.objects.filter(models.Q(code__icontains='ADMIN') | models.Q(description__iexact='admin')):
        for permission in admin_permissions:
            RolePermission.objects.get_or_create(role=role, permission=permission, defaults={'id':str(uuid.uuid4()),'state':True})
    client_role, _ = Role.objects.get_or_create(code='CLIENT_USER', defaults={'id':str(uuid.uuid4()),'name':'Usuario cliente','description':'Acceso al portal de clientes','audience':'CLIENT_PORTAL','is_system':True,'state':True})
    portal_permission = Permission.objects.get(code='client_portal.access')
    RolePermission.objects.get_or_create(role=client_role, permission=portal_permission, defaults={'id':str(uuid.uuid4()),'state':True})


class Migration(migrations.Migration):
    dependencies = [('authentication', '0006_alter_user_phone_number')]
    operations = [
        migrations.AddField(model_name='role', name='audience', field=models.CharField(choices=[('INTERNAL','Internal'),('CLIENT_PORTAL','Client portal')], default='INTERNAL', max_length=20)),
        migrations.AddField(model_name='role', name='code', field=models.CharField(blank=True, max_length=80, null=True)),
        migrations.AddField(model_name='role', name='is_system', field=models.BooleanField(default=False)),
        migrations.AddField(model_name='role', name='name', field=models.CharField(blank=True, max_length=120, null=True)),
        migrations.CreateModel(name='Permission', fields=[('id',models.CharField(editable=False,max_length=255,primary_key=True,serialize=False,unique=True)),('state',models.BooleanField(default=True)),('created_at',models.DateTimeField(auto_now_add=True)),('updated_at',models.DateTimeField(default=None,null=True)),('code',models.CharField(max_length=120,unique=True)),('module',models.CharField(max_length=80)),('action',models.CharField(max_length=40)),('name',models.CharField(max_length=160)),('description',models.TextField(blank=True,null=True)),('user_created_at',models.ForeignKey(default=None,null=True,on_delete=django.db.models.deletion.CASCADE,related_name='%(class)s_created_at',to=settings.AUTH_USER_MODEL)),('user_updated_at',models.ForeignKey(default=None,null=True,on_delete=django.db.models.deletion.CASCADE,related_name='%(class)s_updated_at',to=settings.AUTH_USER_MODEL))], options={'db_table':'permissions','ordering':['module','action']}),
        migrations.CreateModel(name='RolePermission', fields=[('id',models.CharField(editable=False,max_length=255,primary_key=True,serialize=False,unique=True)),('state',models.BooleanField(default=True)),('created_at',models.DateTimeField(auto_now_add=True)),('updated_at',models.DateTimeField(default=None,null=True)),('permission',models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name='role_assignments',to='authentication.permission')),('role',models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name='permission_assignments',to='authentication.role')),('user_created_at',models.ForeignKey(default=None,null=True,on_delete=django.db.models.deletion.CASCADE,related_name='%(class)s_created_at',to=settings.AUTH_USER_MODEL)),('user_updated_at',models.ForeignKey(default=None,null=True,on_delete=django.db.models.deletion.CASCADE,related_name='%(class)s_updated_at',to=settings.AUTH_USER_MODEL))], options={'db_table':'role_permissions'}),
        migrations.RunPython(seed_rbac, migrations.RunPython.noop),
        migrations.AlterField(model_name='role', name='code', field=models.CharField(blank=True,max_length=80,null=True,unique=True)),
        migrations.AddConstraint(model_name='rolepermission', constraint=models.UniqueConstraint(fields=('role','permission'),name='uniq_role_permission')),
        migrations.AddConstraint(model_name='userrole', constraint=models.UniqueConstraint(fields=('user','role'),name='uniq_user_role')),
    ]
