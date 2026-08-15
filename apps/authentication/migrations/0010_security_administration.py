import uuid
from django.db import migrations

PERMISSIONS=[
 ('security.access','security','access','Acceder a configuración de seguridad'),
 ('permissions.view','permissions','view','Ver catálogo de permisos'),
 ('permissions.manage','permissions','manage','Administrar catálogo de permisos'),
 ('roles.assign_permissions','roles','assign_permissions','Asignar permisos a roles'),
]

def seed(apps,schema_editor):
    Permission,Role,RolePermission=(apps.get_model('authentication',n) for n in ('Permission','Role','RolePermission'))
    created=[]
    for code,module,action,name in PERMISSIONS:
        p,_=Permission.objects.get_or_create(code=code,defaults={'id':str(uuid.uuid4()),'module':module,'action':action,'name':name,'state':True}); created.append(p)
    role,_=Role.objects.get_or_create(code='SECURITY_ADMIN',defaults={'id':str(uuid.uuid4()),'name':'Administrador de seguridad','description':'Gestiona roles, permisos y auditoría de seguridad','audience':'INTERNAL','is_system':True,'state':True})
    codes=['security.access','permissions.view','permissions.manage','roles.view','roles.create','roles.update','roles.delete','roles.assign_permissions','audit.view','audit.export']
    for permission in Permission.objects.filter(code__in=codes):
        RolePermission.objects.get_or_create(role=role,permission=permission,defaults={'id':str(uuid.uuid4()),'state':True})
    user_admin,_=Role.objects.get_or_create(code='USER_ADMIN',defaults={'id':str(uuid.uuid4()),'name':'Administrador de usuarios','description':'Crea usuarios, asigna roles y gestiona cuentas de clientes sin modificar la configuración de seguridad','audience':'INTERNAL','is_system':True,'state':True})
    user_codes=['users.view','users.create','users.update','users.block','users.assign_roles','client_access.view','client_access.create','client_access.update','client_access.block','roles.view']
    for permission in Permission.objects.filter(code__in=user_codes):
        RolePermission.objects.get_or_create(role=user_admin,permission=permission,defaults={'id':str(uuid.uuid4()),'state':True})
    for admin in Role.objects.filter(code__icontains='ADMIN').exclude(code='USER_ADMIN'):
        for permission in created:
            RolePermission.objects.get_or_create(role=admin,permission=permission,defaults={'id':str(uuid.uuid4()),'state':True})

class Migration(migrations.Migration):
    dependencies=[('authentication','0009_access_audit')]
    operations=[migrations.RunPython(seed,migrations.RunPython.noop)]
