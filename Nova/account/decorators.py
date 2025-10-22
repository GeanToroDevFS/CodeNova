from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from functools import wraps


def login_required_custom(view_func):
    """
    Decorador personalizado para verificar autenticación.
    Usa el decorador login_required de Django con redirección al login.
    """
    return login_required(login_url='login')(view_func)


def _user_has_permission(user, module: str, action: str) -> bool:
    """Devuelve True si el usuario tiene el permiso específico 'modulo_accion'."""
    if not user or not user.is_authenticated or not getattr(user, 'estado', True):
        return False
    if user.is_superuser:
        return True
    rol = getattr(user, 'rol', None)
    if not rol or not getattr(rol, 'estado', True):  # 🚫 Rol inactivo no tiene permisos
        return False
    perms = rol.get_permisos_list() or []
    target = f"{module.strip().lower()}_{action.strip().lower()}"
    return target in perms


def role_required(roles=None, allowed_perms=None, module=None, action=None):
    """
    Decorador flexible para validar acceso según:
      - roles: nombres de rol (compatibilidad)
      - allowed_perms: lista de permisos exactos (ej. ['gestionar_usuarios'])
      - module + action: permisos granulares ('almacenes', 'crear')

    Ejemplo granular:
        @role_required(module='almacenes', action='crear')
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Verificación de sesión y usuario activo
            if not request.user.is_authenticated:
                return redirect('login')

            if not getattr(request.user, 'estado', True):
                messages.error(request, 'Tu usuario está inactivo. Contacta con el administrador.')
                return redirect('login')

            # Superuser siempre tiene acceso total
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            user_rol = getattr(request.user, 'rol', None)

            # 🚫 Sin rol asignado
            if not user_rol:
                messages.error(request, 'No tienes un rol asignado. Contacta con el administrador.')
                return redirect('dashboard')

            # 🚫 Rol inactivo
            if hasattr(user_rol, 'estado') and not user_rol.estado:
                messages.error(request, 'Tu rol está inactivo. Contacta con el administrador.')
                return redirect('dashboard')

            # ✅ Compatibilidad con lista de roles antiguos
            if roles:
                rol_nombre = (user_rol.nombre or '').strip().lower()
                if rol_nombre in [r.strip().lower() for r in roles]:
                    return view_func(request, *args, **kwargs)

            # ✅ Permisos exactos (modo clásico)
            if allowed_perms:
                user_perms = user_rol.get_permisos_list()
                if any(perm.strip().lower() in user_perms for perm in allowed_perms):
                    return view_func(request, *args, **kwargs)
                messages.error(request, 'No tienes permisos para acceder a esta sección.')
                return redirect('dashboard')

            # ✅ Permisos granulares (módulo + acción)
            if module and action:
                if _user_has_permission(request.user, module, action):
                    return view_func(request, *args, **kwargs)
                messages.error(request, 'No tienes permisos suficientes para realizar esta acción.')
                return redirect('dashboard')

            # 🚫 Ningún permiso coincide
            messages.error(request, 'No tienes permisos para acceder a esta vista.')
            return redirect('dashboard')

        return wrapper
    return decorator
