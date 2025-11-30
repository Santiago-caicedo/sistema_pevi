from django.core.exceptions import PermissionDenied
from functools import wraps

def role_required(allowed_roles=[]):
    """
    Portero Universal: Solo deja pasar si el rol está en la lista.
    El Superusuario siempre pasa (God Mode).
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # 1. Puerta trasera para Superadmin (Tú)
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            # 2. Verificación de Rol
            if request.user.rol in allowed_roles:
                return view_func(request, *args, **kwargs)
            
            # 3. DEFAULT DENY (Si no cumple, afuera)
            raise PermissionDenied("Acceso Denegado: Tu rol no tiene permisos para esta acción.")
            
        return _wrapped_view
    return decorator

# --- DEFINICIÓN DE PERFILES DE ACCESO ---

# 1. SOLO DIRECTIVOS (Para ver Empresas y Equipo)
# Director de Centro y Director Nacional
def solo_directivos(view_func):
    return role_required(['DIRECTOR_CENTRO', 'DIRECTOR_NACIONAL'])(view_func)

# 2. SOLO LÍDERES (Para Crear Proyectos)
# Directores y Profesores (Los estudiantes NO crean proyectos)
def solo_lideres(view_func):
    return role_required(['DIRECTOR_CENTRO', 'DIRECTOR_NACIONAL', 'PROFESOR'])(view_func)

# 3. ACCESO STAFF (Para ver listas generales)
# Todos menos externos (si los hubiera). Por ahora todos los roles internos.
def acceso_staff(view_func):
    return role_required(['ESTUDIANTE', 'PROFESOR', 'DIRECTOR_CENTRO', 'DIRECTOR_NACIONAL'])(view_func)