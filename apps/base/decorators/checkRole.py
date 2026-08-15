from apps.base.utils.index import response
from apps.authentication.access import get_access_profile, required_permission_for_request, user_has_permission


def checkRole(role):
    def decorator(fun):
        def wrapper(*args, **kwargs):
            try:
                authorized = False
                request = args[1]
                superUser = request.user.is_superuser
                profile = get_access_profile(request.user)
                # check if the role is in the token
                if role:
                    expected = [role] if isinstance(role, str) else role
                    for x in expected:
                        if x in profile['roles']:
                            authorized = True

                # check if the user is authorized
                required_permission = required_permission_for_request(request)
                if authorized or superUser or (required_permission and user_has_permission(request.user, required_permission)):
                    return fun(*args, **kwargs)
                else:
                    return response({'error': True, 'message': 'no autorizado'}, 403)

            except Exception as e:
                if str(e) == "'is_superuser'":
                    return response({'error': True, 'message': 'token de acceso no proveído '}, 401)
                return response({'error': str(e)}, 500)
        return wrapper
    return decorator
