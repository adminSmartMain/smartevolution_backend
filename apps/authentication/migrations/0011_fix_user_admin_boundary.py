from django.db import migrations

def clean_user_admin(apps,schema_editor):
    Role,RolePermission=(apps.get_model('authentication',n) for n in ('Role','RolePermission'))
    role=Role.objects.filter(code='USER_ADMIN').first()
    if role:
        forbidden=['security.access','permissions.view','permissions.manage','roles.create','roles.update','roles.delete','roles.assign_permissions','roles.manage','audit.view','audit.export']
        RolePermission.objects.filter(role=role,permission__code__in=forbidden).delete()

class Migration(migrations.Migration):
    dependencies=[('authentication','0010_security_administration')]
    operations=[migrations.RunPython(clean_user_admin,migrations.RunPython.noop)]
