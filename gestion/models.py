from django.db import models
from django.contrib.auth.models import AbstractUser

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
    
    ROLES_CHOICES = [
        (ROL_ESTUDIANTE, 'Estudiante / Ingeniero Junior'),
        (ROL_PROFESOR, 'Profesor Líder de Proyecto'),
        (ROL_DIRECTOR, 'Director de Centro PEVI'),
        (ROL_NACIONAL, 'Director Nacional (Líder PEVI)'),
    ]

    centro_pevi = models.ForeignKey(CentroPevi, on_delete=models.PROTECT, null=True, blank=True)
    rol = models.CharField(max_length=30, choices=ROLES_CHOICES, default=ROL_ESTUDIANTE)
    cargo = models.CharField(max_length=100, blank=True)

    # Helper properties para usar en los templates fácilmente
    @property
    def es_nacional(self):
        """Es líder nacional o superusuario."""
        return self.rol == self.ROL_NACIONAL or self.is_superuser

    @property
    def es_director_centro(self):
        """
        Devuelve True si:
        1. Su rol es explícitamente Director de Centro.
        2. O SI ES NACIONAL pero tiene un centro asignado (Caso César Acevedo).
        """
        es_director_puro = (self.rol == self.ROL_DIRECTOR)
        es_nacional_con_centro = (self.rol == self.ROL_NACIONAL and self.centro_pevi is not None)
        
        return es_director_puro or es_nacional_con_centro or self.is_superuser

    @property
    def es_profesor(self):
        return self.rol == self.ROL_PROFESOR
    
    @property
    def es_directivo(self):
        """Devuelve True si el usuario tiene capacidad de gestión (Director o Nacional)."""
        return self.rol in [self.ROL_DIRECTOR, self.ROL_NACIONAL] or self.is_superuser

    def __str__(self):
        return f"{self.username} - {self.get_rol_display()}"