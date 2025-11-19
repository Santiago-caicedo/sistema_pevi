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
    """
    Modelo de usuario personalizado para el sistema PEVI.
    Reemplaza al usuario por defecto de Django.
    """
    # Definimos los roles como constantes
    ROL_ADMIN = 'ADMIN'
    ROL_LIDER = 'LIDER'
    ROL_INGENIERO = 'INGENIERO'

    ROLES_CHOICES = [
        (ROL_ADMIN, 'Administrador Global (UPME)'),
        (ROL_LIDER, 'Líder de Centro'),
        (ROL_INGENIERO, 'Ingeniero / Estudiante'),
    ]

    # Campos personalizados
    centro_pevi = models.ForeignKey(
        CentroPevi, 
        on_delete=models.PROTECT, 
        null=True, 
        blank=True, 
        related_name="usuarios",
        help_text="A qué universidad pertenece este usuario"
    )
    rol = models.CharField(max_length=20, choices=ROLES_CHOICES, default=ROL_INGENIERO)
    cargo = models.CharField(max_length=100, blank=True, help_text="Ej: Docente Coordinador, Tesista")

    def __str__(self):
        return f"{self.username} - {self.get_rol_display()}"