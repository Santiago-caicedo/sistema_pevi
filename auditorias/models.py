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



# ==========================================
#  CORE DE ENERGÉTICOS: POLIMORFISMO
# ==========================================

class FuenteEnergiaBase(models.Model):
    """
    Clase Abstracta que define lo que TODAS las energías tienen en común.
    No crea una tabla en la BD, sirve de plantilla.
    """
    proyecto = models.ForeignKey(ProyectoAuditoria, on_delete=models.CASCADE, related_name="%(class)s_related")
    
    # Datos Económicos y de Consumo (Inputs del Usuario)
    consumo_promedio_mensual = models.FloatField(verbose_name="Consumo Mensual Promedio")
    consumo_total_anual = models.FloatField(verbose_name="Consumo Total Anual")
    
    costo_unitario = models.FloatField(verbose_name="Costo Unitario Promedio ($/Unidad)")
    costo_total_anual = models.FloatField(verbose_name="Costo Total Anual ($)")
    
    # Datos Ambientales (Input del Usuario o Sugerido)
    factor_emision = models.FloatField(help_text="Factor de Emisión (kgCO2/Unidad)", verbose_name="FE")

    class Meta:
        abstract = True

    def calcular_emisiones_ton_co2(self):
        """Calcula Toneladas de CO2 al año: (Consumo * FE) / 1000"""
        return (self.consumo_total_anual * self.factor_emision) / 1000

    def save(self, *args, **kwargs):
        # Pequeña validación de integridad: Si no ponen el total anual, lo estimamos
        if not self.consumo_total_anual and self.consumo_promedio_mensual:
            self.consumo_total_anual = self.consumo_promedio_mensual * 12
        if not self.costo_total_anual and self.consumo_total_anual and self.costo_unitario:
            self.costo_total_anual = self.consumo_total_anual * self.costo_unitario
        super().save(*args, **kwargs)


class Electricidad(FuenteEnergiaBase):
    """
    La electricidad es única: ya viene en kWh y no tiene Poder Calorífico.
    Unidad: kWh
    """
    # No necesita campos extra, usa los de la base.
    
    def get_kwh_equivalente(self):
        return self.consumo_total_anual

    class Meta:
        verbose_name = "Electricidad"
        verbose_name_plural = "Electricidad"

    def __str__(self):
        return f"Elec - {self.consumo_total_anual} kWh"


class CombustibleBase(FuenteEnergiaBase):
    """
    Clase Abstracta para todo lo que se quema (Gas, Carbón, Diesel).
    Estos SÍ requieren Poder Calorífico (PC) para convertirse a energía útil.
    """
    poder_calorifico = models.FloatField(verbose_name="Poder Calorífico (PC)", help_text="Energía por unidad de masa/volumen")
    unidad_pc = models.CharField(max_length=20, help_text="Ej: MJ/kg, kJ/m3, kWh/gal")

    class Meta:
        abstract = True

    def get_kwh_equivalente(self):
        """
        Normalización crítica: Convierte el combustible a kWh teóricos.
        Nota: Esta es una simplificación, en producción requerirá un convertidor de unidades robusto 
        según la unidad del PC (MJ vs kWh). Por ahora asumiremos conversión directa si PC está en kWh/unidad,
        o conversión estándar de MJ a kWh (1 MJ = 0.277 kWh).
        """
        # Lógica simplificada: Si el PC viene en MJ, convertir a kWh
        factor_conversion = 1.0
        if 'MJ' in self.unidad_pc:
            factor_conversion = 0.277778
        elif 'kJ' in self.unidad_pc:
            factor_conversion = 0.000277778
            
        energia_total = self.consumo_total_anual * self.poder_calorifico * factor_conversion
        return energia_total


# --- MODELOS CONCRETOS (TABLAS REALES) ---

class GasNatural(CombustibleBase):
    """ Unidad: Metros Cúbicos (m3) """
    unidad_medida = "m³"
    
    class Meta:
        verbose_name = "Gas Natural"
        verbose_name_plural = "Gas Natural"

class CarbonMineral(CombustibleBase):
    """ Unidad: Toneladas """
    unidad_medida = "Ton"

    class Meta:
        verbose_name = "Carbón Mineral"
        verbose_name_plural = "Carbón Mineral"

class FuelOil(CombustibleBase):
    """ Unidad: Galones """
    unidad_medida = "Gal"

    class Meta:
        verbose_name = "Fuel Oil / Diesel"
        verbose_name_plural = "Fuel Oil / Diesel"

class Biomasa(CombustibleBase):
    """ Unidad: Toneladas (Madera, Bagazo, Cascarilla) """
    tipo_biomasa = models.CharField(max_length=50, default="Genérica", help_text="Ej: Bagazo, Cisco, Leña")
    unidad_medida = "Ton"

    class Meta:
        verbose_name = "Biomasa / Bagazo"
        verbose_name_plural = "Biomasa"

class GasPropano(CombustibleBase):
    """ Unidad: Kilogramos (kg) o Galones """
    unidad_medida = "kg" # Estandarizamos a masa según tu texto corregido

    class Meta:
        verbose_name = "Gas Propano (GLP)"
        verbose_name_plural = "Gas Propano (GLP)"