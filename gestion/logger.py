"""
Sistema de Logging para PEVI.
Proporciona funciones simples para registrar eventos en archivos y base de datos.
"""

import logging
from django.utils import timezone

# Obtener los loggers configurados en settings.py
logger_acceso = logging.getLogger('pevi.acceso')
logger_actividad = logging.getLogger('pevi.actividad')
logger_seguridad = logging.getLogger('pevi.seguridad')
logger_errores = logging.getLogger('pevi.errores')


def get_client_ip(request):
    """Obtiene la IP real del cliente (considera proxies)."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_user_agent(request):
    """Obtiene el User-Agent del navegador."""
    return request.META.get('HTTP_USER_AGENT', '')[:500]


def _guardar_en_db(tipo, accion, usuario=None, request=None, **kwargs):
    """Guarda el registro en la base de datos."""
    from .models import RegistroActividad

    try:
        registro = RegistroActividad(
            tipo=tipo,
            accion=accion,
            usuario=usuario if usuario and usuario.is_authenticated else None,
            username_intento=kwargs.get('username_intento', ''),
            modelo_afectado=kwargs.get('modelo', ''),
            objeto_id=kwargs.get('objeto_id'),
            objeto_repr=kwargs.get('objeto_repr', '')[:200],
            descripcion=kwargs.get('descripcion', ''),
            ip_address=get_client_ip(request) if request else None,
            user_agent=get_user_agent(request) if request else '',
            centro=usuario.centro_pevi if usuario and hasattr(usuario, 'centro_pevi') else None,
        )
        registro.save()
        return registro
    except Exception as e:
        logger_errores.error(f"Error guardando log en BD: {e}")
        return None


# ==============================================================================
# LOGS DE ACCESO
# ==============================================================================

def log_login(request, usuario):
    """Registra un login exitoso."""
    ip = get_client_ip(request)
    mensaje = f"LOGIN exitoso | Usuario: {usuario.username} | Rol: {usuario.get_rol_display()} | IP: {ip}"
    logger_acceso.info(mensaje)

    _guardar_en_db(
        tipo='ACCESO',
        accion='LOGIN',
        usuario=usuario,
        request=request,
        descripcion=f"Inicio de sesión desde {ip}"
    )


def log_logout(request, usuario):
    """Registra un logout."""
    ip = get_client_ip(request)
    mensaje = f"LOGOUT | Usuario: {usuario.username} | IP: {ip}"
    logger_acceso.info(mensaje)

    _guardar_en_db(
        tipo='ACCESO',
        accion='LOGOUT',
        usuario=usuario,
        request=request,
        descripcion=f"Cierre de sesión desde {ip}"
    )


def log_login_fallido(request, username):
    """Registra un intento de login fallido."""
    ip = get_client_ip(request)
    mensaje = f"LOGIN FALLIDO | Username intentado: {username} | IP: {ip}"
    logger_acceso.warning(mensaje)
    logger_seguridad.warning(mensaje)

    _guardar_en_db(
        tipo='SEGURIDAD',
        accion='LOGIN_FALLIDO',
        request=request,
        username_intento=username,
        descripcion=f"Intento fallido de login con usuario '{username}' desde {ip}"
    )


# ==============================================================================
# LOGS DE ACTIVIDAD (CRUD)
# ==============================================================================

def log_crear(request, modelo, objeto, descripcion=''):
    """Registra la creación de un objeto."""
    usuario = request.user
    mensaje = f"CREAR {modelo} | ID: {objeto.id} | {objeto} | Usuario: {usuario.username}"
    logger_actividad.info(mensaje)

    _guardar_en_db(
        tipo='ACTIVIDAD',
        accion='CREAR',
        usuario=usuario,
        request=request,
        modelo=modelo,
        objeto_id=objeto.id,
        objeto_repr=str(objeto),
        descripcion=descripcion or f"Creó {modelo}: {objeto}"
    )


def log_editar(request, modelo, objeto, cambios=''):
    """Registra la edición de un objeto."""
    usuario = request.user
    mensaje = f"EDITAR {modelo} | ID: {objeto.id} | {objeto} | Usuario: {usuario.username}"
    if cambios:
        mensaje += f" | Cambios: {cambios}"
    logger_actividad.info(mensaje)

    _guardar_en_db(
        tipo='ACTIVIDAD',
        accion='EDITAR',
        usuario=usuario,
        request=request,
        modelo=modelo,
        objeto_id=objeto.id,
        objeto_repr=str(objeto),
        descripcion=cambios or f"Editó {modelo}: {objeto}"
    )


def log_eliminar(request, modelo, objeto_id, objeto_repr):
    """Registra la eliminación de un objeto."""
    usuario = request.user
    mensaje = f"ELIMINAR {modelo} | ID: {objeto_id} | {objeto_repr} | Usuario: {usuario.username}"
    logger_actividad.info(mensaje)

    _guardar_en_db(
        tipo='ACTIVIDAD',
        accion='ELIMINAR',
        usuario=usuario,
        request=request,
        modelo=modelo,
        objeto_id=objeto_id,
        objeto_repr=objeto_repr,
        descripcion=f"Eliminó {modelo}: {objeto_repr}"
    )


def log_ver(request, modelo, objeto):
    """Registra la visualización de un objeto sensible (opcional)."""
    usuario = request.user
    mensaje = f"VER {modelo} | ID: {objeto.id} | Usuario: {usuario.username}"
    logger_actividad.info(mensaje)


# ==============================================================================
# LOGS DE SEGURIDAD
# ==============================================================================

def log_acceso_denegado(request, recurso, razon=''):
    """Registra un intento de acceso denegado."""
    usuario = request.user if request.user.is_authenticated else None
    ip = get_client_ip(request)
    username = usuario.username if usuario else 'Anónimo'

    mensaje = f"ACCESO DENEGADO | Usuario: {username} | Recurso: {recurso} | IP: {ip}"
    if razon:
        mensaje += f" | Razón: {razon}"

    logger_seguridad.warning(mensaje)

    _guardar_en_db(
        tipo='SEGURIDAD',
        accion='ACCESO_DENEGADO',
        usuario=usuario,
        request=request,
        descripcion=f"Intento de acceso a {recurso}. {razon}"
    )


def log_escalada_bloqueada(request, accion_intentada):
    """Registra un intento de escalada de privilegios bloqueado."""
    usuario = request.user
    ip = get_client_ip(request)

    mensaje = f"ESCALADA BLOQUEADA | Usuario: {usuario.username} | Rol: {usuario.rol} | Acción: {accion_intentada} | IP: {ip}"
    logger_seguridad.error(mensaje)

    _guardar_en_db(
        tipo='SEGURIDAD',
        accion='ESCALADA_BLOQUEADA',
        usuario=usuario,
        request=request,
        descripcion=f"Intento de escalada: {accion_intentada}"
    )


def log_cambio_estado(request, proyecto, estado_anterior, estado_nuevo):
    """Registra cambios de estado en proyectos."""
    usuario = request.user
    mensaje = f"CAMBIO ESTADO | Proyecto: {proyecto.id} | {estado_anterior} -> {estado_nuevo} | Usuario: {usuario.username}"
    logger_actividad.info(mensaje)

    _guardar_en_db(
        tipo='ACTIVIDAD',
        accion='EDITAR',
        usuario=usuario,
        request=request,
        modelo='ProyectoAuditoria',
        objeto_id=proyecto.id,
        objeto_repr=str(proyecto),
        descripcion=f"Cambió estado de {estado_anterior} a {estado_nuevo}"
    )


# ==============================================================================
# LOGS DE ERRORES
# ==============================================================================

def log_error(request, error, contexto=''):
    """Registra un error del sistema."""
    usuario = request.user if request and request.user.is_authenticated else None
    ip = get_client_ip(request) if request else 'N/A'

    mensaje = f"ERROR | {error} | Usuario: {usuario.username if usuario else 'N/A'} | IP: {ip}"
    if contexto:
        mensaje += f" | Contexto: {contexto}"

    logger_errores.error(mensaje)

    if request:
        _guardar_en_db(
            tipo='ERROR',
            accion='VER',  # Usamos VER como placeholder
            usuario=usuario,
            request=request,
            descripcion=f"Error: {error}. Contexto: {contexto}"
        )
