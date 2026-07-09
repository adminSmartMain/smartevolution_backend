from functools import wraps
from rest_framework.response import Response
from rest_framework.permissions import BasePermission
from django.conf import settings

PUBLIC_PREFIXES = ('/api/auth/login', '/api/auth/forgot', '/api/auth/reset', '/api/auth/check', '/api/auth/token/verify/', '/api/auth/password-reset/', '/api/selfManagement/', '/api/schema/', '/api/docs/', '/api/redoc/')
PREFIX_MODULES = (
    ('/api/access-control/', 'access_control'), ('/api/client/client-roles', 'client_roles'),
    ('/api/client/client-role-assignments', 'client_roles'), ('/api/client/', 'clients'),
    ('/api/contact/', 'clients'), ('/api/legalRepresentative/', 'clients'), ('/api/overview/', 'clients'),
    ('/api/technicalData/', 'clients'), ('/api/request/', 'prospects'), ('/api/riskProfile/', 'risk_profiles'),
    ('/api/financialProfile/', 'financial_profiles'), ('/api/account/', 'client_accounts'),
    ('/api/broker/', 'brokers'), ('/api/bill/', 'bills'), ('/api/preOperation/', 'preoperations'),
    ('/api/receipt/', 'receipts'), ('/api/buyOrder/', 'operations'), ('/api/integration/', 'integrations'),
    ('/api/dashboard', 'dashboard'), ('/api/deposit/', 'deposits'), ('/api/emitter-deposit/', 'deposits'),
    ('/api/refund/', 'refunds'), ('/api/report/negotiationSummary/', 'negotiations'),
    ('/api/report/', 'reports'),
)
CATALOG_PREFIXES = ('/api/account_type/','/api/activity/','/api/bank/','/api/ciiu/','/api/city/','/api/department/','/api/section/','/api/type_','/api/country/','/api/accounting_account/','/api/period_range/','/api/receipt_status/')


def required_permission_for_request(request):
    path = request.path
    if path.startswith(PUBLIC_PREFIXES): return None
    if path.startswith('/api/dashboard'): return None
    if path.startswith('/api/access-control/me'): return None
    if path.startswith('/api/access-control/permissions') or path.startswith('/api/access-control/roles'): return 'roles.manage'
    if path.startswith('/api/access-control/users') or path.startswith('/api/access-control/client-access'): return 'users.view' if request.method == 'GET' else 'users.manage'
    module = 'catalogs' if path.startswith(CATALOG_PREFIXES) else next((m for prefix,m in PREFIX_MODULES if path.startswith(prefix)), None)
    if not module: return None
    lowered = path.lower()
    if request.method == 'GET':
        action = 'export' if any(x in lowered for x in ('export','download','pdf','excel')) else 'view'
    elif request.method == 'POST':
        if any(x in lowered for x in ('approve','approval','authorize','verify')): action='approve'
        elif any(x in lowered for x in ('import','massive','upload')): action='import'
        elif any(x in lowered for x in ('void','annul','cancel')): action='void'
        else: action='create'
    elif request.method in ('PUT','PATCH'):
        if any(x in lowered for x in ('approve','approval','authorize','verify')): action='approve'
        elif any(x in lowered for x in ('void','annul','cancel')): action='void'
        else: action='update'
    elif request.method == 'DELETE': action='delete'
    else: action='view'
    code = f'{module}.{action}'
    # Modules whose special action is intentionally represented by a broader permission.
    fallbacks = {'client_roles.view':'clients.assign_roles','client_roles.create':'clients.assign_roles','client_roles.update':'clients.assign_roles','client_roles.delete':'clients.assign_roles','access_control.view':'roles.manage'}
    return fallbacks.get(code, code)


class PlatformPermission(BasePermission):
    message = 'No tiene el permiso requerido para esta operación.'
    def has_permission(self, request, view):
        if request.path.startswith(PUBLIC_PREFIXES): return True
        if not request.user or not request.user.is_authenticated: return False
        # A client identity belongs to a different application realm. This rule
        # is intentionally evaluated before superuser/role permissions.
        if hasattr(request.user, 'client_access'):
            return bool(getattr(settings,'CLIENT_PORTAL_ENABLED',False) and request.path.startswith('/api/client-portal/'))
        required = required_permission_for_request(request)
        return True if required is None else user_has_permission(request.user, required)


def get_access_profile(user):
    from apps.authentication.api.models.userRole.index import UserRole
    if not user or not user.is_authenticated:
        return {'roles': [], 'permissions': [], 'client': None, 'client_roles': [], 'account_scope': None, 'client_access_status': None}
    assignments = UserRole.objects.filter(user=user, state=True, role__state=True).select_related('role')
    roles = list(assignments.values_list('role__code', flat=True))
    legacy_roles = list(assignments.values_list('role__description', flat=True))
    permissions = set()
    for assignment in assignments.prefetch_related('role__permission_assignments__permission'):
        permissions.update(
            rp.permission.code for rp in assignment.role.permission_assignments.all()
            if rp.state and rp.permission.state
        )
    client_id, client_roles, account_scope, client_access_status = None, [], 'INTERNAL', None
    access = getattr(user, 'client_access', None)
    if access:
        account_scope, client_access_status = 'CLIENT_PORTAL', access.status
        client_id = access.client_id
        if access.state:
            client_roles = list(access.client.role_assignments.filter(state=True, role__state=True).values_list('role__code', flat=True))
        # Never expose internal permissions to a client identity, even if a
        # role was assigned by mistake.
        permissions = {p for p in permissions if p.startswith('client_portal.')} if getattr(settings,'CLIENT_PORTAL_ENABLED',False) else set()
    return {'roles': sorted(set(filter(None, roles + legacy_roles))), 'permissions': sorted(permissions), 'client': client_id, 'client_roles': client_roles, 'account_scope': account_scope, 'client_access_status': client_access_status, 'client_portal_enabled': bool(getattr(settings,'CLIENT_PORTAL_ENABLED',False))}


def user_has_permission(user, code):
    return bool(user and user.is_authenticated and (user.is_superuser or code in get_access_profile(user)['permissions']))


def permission_required(code):
    def decorator(view_method):
        @wraps(view_method)
        def wrapped(self, request, *args, **kwargs):
            if not user_has_permission(request.user, code):
                return Response({'error': True, 'message': 'No tiene permiso para realizar esta acción.'}, status=403)
            return view_method(self, request, *args, **kwargs)
        return wrapped
    return decorator
