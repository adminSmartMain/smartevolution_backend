import uuid
from django.db import migrations

MODULES = {
 'dashboard': [('view','Ver indicadores y estadísticas')],
 'prospects': [('view','Ver prospectos'),('create','Crear prospectos'),('update','Editar prospectos'),('delete','Eliminar prospectos'),('approve','Aprobar prospectos'),('export','Exportar prospectos')],
 'clients': [('view','Ver clientes'),('create','Crear clientes'),('update','Editar clientes'),('delete','Desactivar clientes'),('assign_roles','Clasificar clientes'),('export','Exportar clientes')],
 'client_accounts': [('view','Ver cuentas de clientes'),('create','Crear cuentas financieras'),('update','Editar cuentas financieras'),('delete','Desactivar cuentas financieras'),('export','Exportar cuentas financieras')],
 'risk_profiles': [('view','Ver perfiles de riesgo'),('create','Crear perfiles de riesgo'),('update','Editar perfiles de riesgo'),('approve','Aprobar perfiles de riesgo'),('export','Exportar perfiles de riesgo')],
 'financial_profiles': [('view','Ver perfiles financieros'),('create','Crear información financiera'),('update','Editar información financiera'),('delete','Eliminar periodos financieros'),('approve','Aprobar información financiera'),('export','Exportar información financiera')],
 'brokers': [('view','Ver corredores'),('create','Crear corredores'),('update','Editar corredores'),('delete','Desactivar corredores'),('export','Exportar corredores')],
 'bills': [('view','Ver facturas'),('create','Registrar facturas'),('update','Editar facturas'),('delete','Eliminar facturas'),('approve','Aprobar facturas'),('import','Importar facturas'),('export','Exportar facturas')],
 'preoperations': [('view','Ver preoperaciones'),('create','Crear preoperaciones'),('update','Editar preoperaciones'),('delete','Eliminar preoperaciones'),('approve','Aprobar preoperaciones'),('import','Importar operaciones masivas'),('export','Exportar preoperaciones')],
 'operations': [('view','Ver operaciones aprobadas'),('create','Crear operaciones'),('update','Editar operaciones'),('delete','Anular operaciones'),('approve','Aprobar operaciones'),('export','Exportar operaciones')],
 'receipts': [('view','Ver recaudos'),('create','Registrar recaudos'),('update','Ajustar recaudos'),('void','Anular recaudos'),('import','Importar recaudos masivos'),('export','Exportar recaudos'),('history','Ver historial de recaudos')],
 'integrations': [('view','Ver integraciones'),('create','Ejecutar integraciones'),('update','Reintentar integraciones'),('export','Exportar resultados de integración')],
 'negotiations': [('view','Ver resúmenes de negociación'),('create','Crear resúmenes de negociación'),('update','Editar resúmenes de negociación'),('approve','Aprobar resúmenes de negociación'),('export','Exportar resúmenes de negociación')],
 'deposits': [('view','Ver giros y depósitos'),('create','Registrar giros y depósitos'),('update','Editar giros y depósitos'),('delete','Eliminar giros y depósitos'),('approve','Aprobar giros y depósitos'),('export','Exportar giros y depósitos')],
 'refunds': [('view','Ver reintegros'),('create','Crear reintegros'),('update','Editar reintegros'),('delete','Eliminar reintegros'),('approve','Aprobar reintegros'),('export','Exportar reintegros')],
 'reports': [('view','Ver reportes y documentos'),('create','Generar reportes y documentos'),('export','Descargar reportes y documentos')],
 'catalogs': [('view','Ver catálogos'),('create','Crear registros de catálogo'),('update','Editar registros de catálogo'),('delete','Eliminar registros de catálogo')],
 'users': [('view','Ver usuarios'),('create','Crear usuarios'),('update','Editar usuarios'),('block','Bloquear o activar usuarios'),('assign_roles','Asignar roles a usuarios'),('manage','Administrar usuarios')],
 'roles': [('view','Ver roles y permisos'),('create','Crear roles'),('update','Editar roles'),('delete','Desactivar roles'),('manage','Gestionar roles y permisos')],
 'client_access': [('view','Ver cuentas de acceso de clientes'),('create','Vincular cuentas de clientes'),('update','Editar cuentas de clientes'),('block','Bloquear cuentas de clientes')],
 'audit': [('view','Ver auditoría de accesos y permisos'),('export','Exportar auditoría')],
 'client_portal': [('access','Acceder al portal de clientes'),('profile','Gestionar perfil propio'),('documents','Gestionar documentos propios'),('operations','Gestionar operaciones propias'),('receipts','Consultar recaudos propios')],
}

ROLE_PRESETS = {
 'OPERATIONS': ['dashboard.view','clients.view','bills.view','bills.create','bills.update','preoperations.view','preoperations.create','preoperations.update','preoperations.approve','preoperations.import','operations.view','operations.create','operations.approve','receipts.view','negotiations.view','reports.view','reports.create','reports.export','catalogs.view'],
 'ACCOUNTING': ['dashboard.view','clients.view','client_accounts.view','operations.view','receipts.view','receipts.create','receipts.update','receipts.void','receipts.import','receipts.export','deposits.view','deposits.create','deposits.update','deposits.approve','refunds.view','refunds.create','refunds.update','refunds.approve','reports.view','reports.create','reports.export','catalogs.view'],
 'COMMERCIAL': ['dashboard.view','prospects.view','prospects.create','prospects.update','clients.view','clients.create','clients.update','clients.assign_roles','brokers.view','brokers.create','brokers.update','bills.view','preoperations.view','reports.view','catalogs.view'],
 'RISK_ANALYST': ['dashboard.view','clients.view','risk_profiles.view','risk_profiles.create','risk_profiles.update','risk_profiles.approve','financial_profiles.view','financial_profiles.create','financial_profiles.update','financial_profiles.approve','reports.view','reports.export','catalogs.view'],
 'AUDITOR': [f'{m}.view' for m in MODULES if m not in ('client_portal',)] + ['audit.view','audit.export','reports.export'],
}

def seed(apps, schema_editor):
    Permission, Role, RolePermission = (apps.get_model('authentication',n) for n in ('Permission','Role','RolePermission'))
    for module, actions in MODULES.items():
        for action, name in actions:
            permission, _ = Permission.objects.get_or_create(code=f'{module}.{action}', defaults={'id':str(uuid.uuid4()),'module':module,'action':action,'name':name,'state':True})
            Permission.objects.filter(pk=permission.pk).update(module=module,action=action,name=name,state=True)
    all_permissions = list(Permission.objects.filter(state=True))
    for role in Role.objects.filter(code__icontains='ADMIN'):
        for permission in all_permissions:
            RolePermission.objects.get_or_create(role=role,permission=permission,defaults={'id':str(uuid.uuid4()),'state':True})
    for code, codes in ROLE_PRESETS.items():
        role,_=Role.objects.get_or_create(code=code,defaults={'id':str(uuid.uuid4()),'name':code.replace('_',' ').title(),'description':f'Perfil base {code}','audience':'INTERNAL','is_system':True,'state':True})
        for permission in Permission.objects.filter(code__in=codes):
            RolePermission.objects.get_or_create(role=role,permission=permission,defaults={'id':str(uuid.uuid4()),'state':True})

class Migration(migrations.Migration):
    dependencies=[('authentication','0007_rbac_permissions')]
    operations=[migrations.RunPython(seed,migrations.RunPython.noop)]
