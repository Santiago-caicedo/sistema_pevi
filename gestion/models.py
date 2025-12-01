from django.db import models
from django.contrib.auth.models import AbstractUser

class CentroPevi(models.Model):
    nombre = models.CharField(max_length=200, unique=True, verbose_name="Universidad / Entidad")
    codigo_interno = models.CharField(max_length=50, unique=True, help_text="Código asignado por UPME")
    region = models.CharField(max_length=100, verbose_name="Región")
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Centro PEVI"
        verbose_name_plural = "Centros PEVI"

    def __str__(self):
        return self.nombre

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