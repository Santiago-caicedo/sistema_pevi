from django.db import models
from django.conf import settings # Para referenciar al Usuario correctamente
from gestion.models import CentroPevi
from django.core.validators import FileExtensionValidator

class Empresa(models.Model):
    """
    Información estática de la empresa cliente.
    """
    razon_social = models.CharField(max_length=200, verbose_name="Razón Social")
    nit = models.CharField(max_length=20, unique=True, verbose_name="NIT")
    sector_productivo = models.CharField(max_length=100, help_text="Ej: Alimentos, Metalmecánica, Textil")
    direccion = models.CharField(max_length=255)
    ciudad = models.CharField(max_length=100)
    
    # Datos de contacto
    contacto_nombre = models.CharField(max_length=150, verbose_name="Nombre Contacto")
    contacto_email = models.EmailField(verbose_name="Email Contacto")
    contacto_telefono = models.CharField(max_length=20, verbose_name="Teléfono")

    def __str__(self):
        return f"{self.razon_social} ({self.nit})"

class ProyectoAuditoria(models.Model):
    """
    La auditoría específica. Vincula un Centro PEVI con una Empresa en un tiempo determinado.
    """
    ESTADOS = [
        ('BORRADOR', 'En Formulación'),
        ('EJECUCION', 'En Ejecución'),
        ('REVISION', 'En Revisión Interna'),
        ('FINALIZADO', 'Finalizado'),
    ]

    # Relaciones
    centro = models.ForeignKey(CentroPevi, on_delete=models.PROTECT, verbose_name="Centro Responsable")
    empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, related_name="auditorias")
    
    # Equipo de trabajo
    lider_proyecto = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name="proyectos_liderados",
        verbose_name="Líder del Proyecto"
    )
    equipo = models.ManyToManyField(
        settings.AUTH_USER_MODEL, 
        related_name="proyectos_asignados", 
        blank=True,
        verbose_name="Ingenieros/Estudiantes Asignados"
    )
    
    # Metadata del Proyecto
    nombre_proyecto = models.CharField(max_length=200, help_text="Ej: Auditoría Energética Planta 1 - 2025")
    fecha_inicio = models.DateField()
    fecha_cierre_estimada = models.DateField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='BORRADOR')
    
    # Contexto Productivo (Para calcular indicadores de intensidad energética después)
    produccion_total = models.FloatField(help_text="Producción total en el periodo evaluado", default=0)
    unidad_produccion = models.CharField(max_length=50, help_text="Ej: Toneladas, Unidades, m2")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.nombre_proyecto} - {self.empresa.razon_social}"

class DocumentoProyecto(models.Model):
    """
    Repositorio de archivos para el proyecto (Informes, Facturas escaneadas, etc)
    """
    proyecto = models.ForeignKey(ProyectoAuditoria, on_delete=models.CASCADE, related_name="documentos")
    archivo = models.FileField(
        upload_to='documentos_proyectos/%Y/%m/',
        validators=[FileExtensionValidator(['pdf', 'xlsx', 'docx', 'jpg', 'png'])]
    )
    descripcion = models.CharField(max_length=100, verbose_name="Nombre del Archivo")
    fecha_subida = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.descripcion