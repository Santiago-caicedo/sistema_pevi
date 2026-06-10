from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

class CentroPevi(models.Model):
    """
    Representa una universidad o entidad participante del programa PEVI.
    Este modelo es protagonista tanto en el portal interno (aislamiento de datos)
    como en la web pública (tarjetas de presentación).
    """

    # =========================================================================
    # IDENTIFICACIÓN
    # =========================================================================
    nombre = models.CharField(max_length=200, unique=True, verbose_name="Nombre Completo")
    nombre_corto = models.CharField(max_length=20, blank=True, verbose_name="Siglas", help_text="Ej: UNAL, UIS, UNINORTE")
    codigo_interno = models.CharField(max_length=50, unique=True, help_text="Código asignado por UPME")
    activo = models.BooleanField(default=True)

    # =========================================================================
    # BRANDING / IMAGEN
    # =========================================================================
    logo = models.ImageField(upload_to='centros/logos/', null=True, blank=True, verbose_name="Logo Institucional")
    imagen_portada = models.ImageField(upload_to='centros/portadas/', null=True, blank=True, verbose_name="Imagen del Campus")
    color_primario = models.CharField(max_length=7, default="#1E40AF", blank=True, verbose_name="Color Institucional", help_text="Código hex, ej: #1E40AF")

    # =========================================================================
    # UBICACIÓN
    # =========================================================================
    region = models.CharField(max_length=100, verbose_name="Región")
    ciudad = models.CharField(max_length=100, blank=True, verbose_name="Ciudad")
    direccion = models.CharField(max_length=255, blank=True, verbose_name="Dirección")
    latitud = models.FloatField(null=True, blank=True, verbose_name="Latitud", help_text="Para mapa interactivo")
    longitud = models.FloatField(null=True, blank=True, verbose_name="Longitud", help_text="Para mapa interactivo")

    # =========================================================================
    # CONTACTO
    # =========================================================================
    email_contacto = models.EmailField(blank=True, verbose_name="Email de Contacto")
    telefono = models.CharField(max_length=30, blank=True, verbose_name="Teléfono")
    sitio_web = models.URLField(blank=True, verbose_name="Sitio Web")

    # =========================================================================
    # REDES SOCIALES
    # =========================================================================
    linkedin = models.URLField(blank=True, verbose_name="LinkedIn")
    twitter = models.URLField(blank=True, verbose_name="Twitter / X")
    instagram = models.URLField(blank=True, verbose_name="Instagram")

    # =========================================================================
    # DESCRIPCIÓN Y CAPACIDADES
    # =========================================================================
    descripcion = models.TextField(blank=True, verbose_name="Descripción", help_text="Descripción del centro y sus capacidades")
    especialidades = models.CharField(max_length=255, blank=True, verbose_name="Especialidades", help_text="Ej: Térmica, Eléctrica, Renovables")
    año_vinculacion = models.PositiveIntegerField(null=True, blank=True, verbose_name="Año de Vinculación", help_text="Año en que se unió al programa PEVI")

    # =========================================================================
    # EQUIPO DIRECTIVO
    # =========================================================================
    director_nombre = models.CharField(max_length=150, blank=True, verbose_name="Nombre del Director")
    director_cargo = models.CharField(max_length=100, blank=True, verbose_name="Cargo Académico", help_text="Ej: PhD. Ingeniería Mecánica")
    director_foto = models.ImageField(upload_to='centros/directores/', null=True, blank=True, verbose_name="Foto del Director")
    director_email = models.EmailField(blank=True, verbose_name="Email del Director")

    # =========================================================================
    # MÉTRICAS (opcionales, se pueden calcular automáticamente)
    # =========================================================================
    estudiantes_formados = models.PositiveIntegerField(default=0, verbose_name="Estudiantes Formados")

    class Meta:
        verbose_name = "Centro PEVI"
        verbose_name_plural = "Centros PEVI"
        ordering = ['nombre']

    def __str__(self):
        if self.nombre_corto:
            return f"{self.nombre_corto} - {self.nombre}"
        return self.nombre

    @property
    def proyectos_count(self):
        """Cantidad de proyectos del centro."""
        return self.proyectoauditoria_set.count()

    @property
    def proyectos_finalizados_count(self):
        """Cantidad de proyectos finalizados."""
        return self.proyectoauditoria_set.filter(estado='FINALIZADO').count()

    @property
    def empresas_atendidas_count(self):
        """Cantidad de empresas únicas atendidas."""
        return self.proyectoauditoria_set.values('empresa').distinct().count()

class Usuario(AbstractUser):
    # DEFINICIÓN DE ROLES (Jerarquía de Gobernanza)
    ROL_ESTUDIANTE = 'ESTUDIANTE'
    ROL_PROFESOR = 'PROFESOR'
    ROL_DIRECTOR = 'DIRECTOR_CENTRO'
    ROL_NACIONAL = 'DIRECTOR_NACIONAL' # Director PEVI Líder (Ve todo)
    ROL_COORDINADOR = 'COORDINADOR' # Coordinador General: admin del panel + anclado a un centro

    ROLES_CHOICES = [
        (ROL_ESTUDIANTE, 'Estudiante / Ingeniero Junior'),
        (ROL_PROFESOR, 'Profesor Líder de Proyecto'),
        (ROL_DIRECTOR, 'Director de Centro PEVI'),
        (ROL_NACIONAL, 'Director Nacional (Líder PEVI)'),
        (ROL_COORDINADOR, 'Coordinador General'),
    ]

    centro_pevi = models.ForeignKey(CentroPevi, on_delete=models.PROTECT, null=True, blank=True)
    rol = models.CharField(max_length=30, choices=ROLES_CHOICES, default=ROL_ESTUDIANTE)
    cargo = models.CharField(max_length=100, blank=True)

    # Helper properties para usar en los templates fácilmente
    @property
    def es_nacional(self):
        """Ve todo el país: líder nacional, coordinador general o superusuario."""
        return self.rol in (self.ROL_NACIONAL, self.ROL_COORDINADOR) or self.is_superuser

    @property
    def es_director_centro(self):
        """
        Devuelve True si:
        1. Su rol es explícitamente Director de Centro.
        2. O SI ES NACIONAL/COORDINADOR pero tiene un centro asignado (patrón híbrido).
        """
        es_director_puro = (self.rol == self.ROL_DIRECTOR)
        es_hibrido_con_centro = (
            self.rol in (self.ROL_NACIONAL, self.ROL_COORDINADOR)
            and self.centro_pevi is not None
        )

        return es_director_puro or es_hibrido_con_centro or self.is_superuser

    @property
    def es_profesor(self):
        return self.rol == self.ROL_PROFESOR

    @property
    def es_directivo(self):
        """Devuelve True si el usuario tiene capacidad de gestión (Director, Nacional o Coordinador)."""
        return self.rol in [self.ROL_DIRECTOR, self.ROL_NACIONAL, self.ROL_COORDINADOR] or self.is_superuser

    @property
    def puede_panel_control(self):
        """Acceso al Panel de Control de la app (no al /admin/ de Django)."""
        return self.is_superuser or self.rol == self.ROL_COORDINADOR

    def __str__(self):
        return f"{self.username} - {self.get_rol_display()}"


class RegistroActividad(models.Model):
    """
    Modelo para almacenar logs de actividad en la base de datos.
    Permite consultas, filtros y reportes de auditoría.
    """

    # Tipos de evento
    TIPO_ACCESO = 'ACCESO'
    TIPO_ACTIVIDAD = 'ACTIVIDAD'
    TIPO_SEGURIDAD = 'SEGURIDAD'
    TIPO_ERROR = 'ERROR'

    TIPOS = [
        (TIPO_ACCESO, 'Acceso'),
        (TIPO_ACTIVIDAD, 'Actividad'),
        (TIPO_SEGURIDAD, 'Seguridad'),
        (TIPO_ERROR, 'Error'),
    ]

    # Acciones comunes
    ACCION_LOGIN = 'LOGIN'
    ACCION_LOGOUT = 'LOGOUT'
    ACCION_LOGIN_FALLIDO = 'LOGIN_FALLIDO'
    ACCION_CREAR = 'CREAR'
    ACCION_EDITAR = 'EDITAR'
    ACCION_ELIMINAR = 'ELIMINAR'
    ACCION_VER = 'VER'
    ACCION_ACCESO_DENEGADO = 'ACCESO_DENEGADO'
    ACCION_ESCALADA_BLOQUEADA = 'ESCALADA_BLOQUEADA'

    ACCIONES = [
        (ACCION_LOGIN, 'Inicio de sesión'),
        (ACCION_LOGOUT, 'Cierre de sesión'),
        (ACCION_LOGIN_FALLIDO, 'Intento de login fallido'),
        (ACCION_CREAR, 'Crear'),
        (ACCION_EDITAR, 'Editar'),
        (ACCION_ELIMINAR, 'Eliminar'),
        (ACCION_VER, 'Ver'),
        (ACCION_ACCESO_DENEGADO, 'Acceso denegado'),
        (ACCION_ESCALADA_BLOQUEADA, 'Escalada de privilegios bloqueada'),
    ]

    # Campos principales
    tipo = models.CharField(max_length=20, choices=TIPOS, db_index=True)
    accion = models.CharField(max_length=30, choices=ACCIONES, db_index=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    # Usuario que realizó la acción (puede ser null si es login fallido)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='actividades'
    )
    username_intento = models.CharField(
        max_length=150,
        blank=True,
        help_text="Username usado en intentos fallidos de login"
    )

    # Contexto de la acción
    modelo_afectado = models.CharField(max_length=50, blank=True, help_text="Ej: Proyecto, Empresa, Usuario")
    objeto_id = models.PositiveIntegerField(null=True, blank=True, help_text="ID del objeto afectado")
    objeto_repr = models.CharField(max_length=200, blank=True, help_text="Representación del objeto")

    # Detalles adicionales
    descripcion = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)

    # Centro PEVI (para filtrar por centro)
    centro = models.ForeignKey(
        CentroPevi,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='actividades'
    )

    class Meta:
        verbose_name = "Registro de Actividad"
        verbose_name_plural = "Registros de Actividad"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['tipo', 'timestamp']),
            models.Index(fields=['usuario', 'timestamp']),
            models.Index(fields=['accion', 'modelo_afectado']),
        ]

    def __str__(self):
        usuario_str = self.usuario.username if self.usuario else self.username_intento or 'Anónimo'
        return f"[{self.timestamp:%Y-%m-%d %H:%M}] {usuario_str} - {self.get_accion_display()}"