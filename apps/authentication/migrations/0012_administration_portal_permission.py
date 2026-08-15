import uuid
from django.db import migrations

def seed(apps,schema_editor):
    Permission,Role,RolePermission=(apps.get_model('authentication',n) for n in ('Permission','Role','RolePermission'))
    permission,_=Permission.objects.get_or_create(code='administration.access',defaults={'id':str(uuid.uuid4()),'module':'administration','action':'access','name':'Acceder al portal de Administración','state':True})
    for role in Role.objects.filter(code__in=['ADMIN','OPERATIONS','ACCOUNTING','COMMERCIAL','USER_ADMIN','SECURITY_ADMIN']):
        RolePermission.objects.get_or_create(role=role,permission=permission,defaults={'id':str(uuid.uuid4()),'state':True})

class Migration(migrations.Migration):
    dependencies=[('authentication','0011_fix_user_admin_boundary')]
    operations=[migrations.RunPython(seed,migrations.RunPython.noop)]
