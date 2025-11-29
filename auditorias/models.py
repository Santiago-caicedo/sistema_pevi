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
    produccion_total = models.FloatField(
        help_text="Producción total en el periodo evaluado", 
        default=0, 
        null=True,  # <--- IMPORTANTE
        blank=True  # <--- IMPORTANTE
    )
    unidad_produccion = models.CharField(
        max_length=50, 
        help_text="Ej: Toneladas, Unidades, m2", 
        null=True,  # <--- IMPORTANTE
        blank=True  # <--- IMPORTANTE
    )

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
#  CORE DE REGISTRO MANUAL (BITÁCORA)
# ==========================================

class FuenteEnergiaBase(models.Model):
    """
    Plantilla base para datos comunes (Costos y Emisiones Finales).
    Ahora TODO es editable.
    """
    proyecto = models.ForeignKey(ProyectoAuditoria, on_delete=models.CASCADE, related_name="%(class)s_related")
    
    # --- 1. DATOS ECONÓMICOS (Manuales) ---
    costo_unitario = models.FloatField(verbose_name="Costo Unitario Promedio", help_text="COP/Unidad")
    costo_mensual_promedio = models.FloatField(verbose_name="Costo Mensual Promedio (COP)")
    costo_total_anual = models.FloatField(verbose_name="Costo Total Anual (COP)")

    # --- 2. DATOS AMBIENTALES (Manuales) ---
    factor_emision = models.FloatField(verbose_name="Factor de Emisión (FE)", help_text="kgCO2/Unidad")
    emisiones_totales = models.FloatField(verbose_name="Emisiones Totales (TonCO2/año)")

    class Meta:
        abstract = True

class Electricidad(FuenteEnergiaBase):
    """ Campos específicos del Excel para Electricidad """
    consumo_mensual = models.FloatField(verbose_name="Consumo Mensual (kWh/mes)")
    consumo_anual = models.FloatField(verbose_name="Consumo Anual (kWh/año)")
    
    # La electricidad no tiene conversión de unidades ni PC complejo
    
    def get_kwh_equivalente(self):
        return self.consumo_anual # Ya viene en kWh

    def calcular_emisiones_ton_co2(self):
        return self.emisiones_totales # Retornamos el valor manual

    class Meta:
        verbose_name = "Registro Electricidad"

class CombustibleBase(FuenteEnergiaBase):
    """ 
    Plantilla para Gas, Carbón, Diesel, etc.
    Incluye las columnas de conversión energética que están en el Excel.
    """
    # Consumo en unidad ORIGINAL (m3, Ton, Gal)
    consumo_mensual_orig = models.FloatField(verbose_name="Consumo Mensual (Ud. Original)")
    consumo_anual_orig = models.FloatField(verbose_name="Consumo Anual (Ud. Original)")
    
    # Datos Técnicos
    poder_calorifico = models.FloatField(verbose_name="Poder Calorífico (PC)", help_text="Unidad Estandarizada: kJ/m³ (Gases/Líq) o kJ/kg (Sólidos)")
    unidad_pc = models.CharField(max_length=20, default="Estándar", editable=False)
    
    # Consumo Convertido (Las columnas 'Consumo kWh.GN/mes' del Excel)
    consumo_mensual_kwh = models.FloatField(verbose_name="Consumo Eq. Mensual (kWh)")
    consumo_anual_kwh = models.FloatField(verbose_name="Consumo Eq. Anual (kWh)")
    
    # Indicador económico normalizado ($COP/kWh)
    costo_kwh_equivalente = models.FloatField(verbose_name="Costo Equivalente ($/kWh)")

    class Meta:
        abstract = True
    

    def save(self, *args, **kwargs):
        # CÁLCULO AUTOMÁTICO DE ENERGÍA (kWh)
        # Fórmula Base: Energía (kJ) = Cantidad * PC
        # Energía (kWh) = Energía (kJ) / 3600
        
        factor_conversion_unidad = 1.0
        
        # CASO ESPECIAL: Fuel Oil (Entra en Galones, PC en kJ/m3)
        # 1 Galón = 0.00378541 m3
        if self._meta.model_name == 'fueloil':
             factor_conversion_unidad = 0.00378541
        
        # CASO ESPECIAL: Carbón/Biomasa (Entra en Toneladas, PC en kJ/kg)
        # 1 Tonelada = 1000 kg
        elif self._meta.model_name in ['carbonmineral', 'biomasa']:
            factor_conversion_unidad = 1000.0
            
        # Gas Natural entra en m3 y PC en kJ/m3 -> Factor 1.0
        # GLP entra en kg y PC en kJ/kg -> Factor 1.0

        if self.consumo_anual_orig and self.poder_calorifico:
            # 1. Calculamos energía total en kJ
            energia_kj = (self.consumo_anual_orig * factor_conversion_unidad) * self.poder_calorifico
            
            # 2. Convertimos a kWh (1 kWh = 3600 kJ)
            self.consumo_anual_kwh = energia_kj / 3600
            
            # 3. Calculamos indicador de costo
            if self.costo_total_anual and self.consumo_anual_kwh > 0:
                self.costo_kwh_equivalente = self.costo_total_anual / self.consumo_anual_kwh
        
        super().save(*args, **kwargs)
        
    def get_kwh_equivalente(self):
        return self.consumo_anual_kwh
        
    def calcular_emisiones_ton_co2(self):
        return self.emisiones_totales

# --- MODELOS CONCRETOS ---
# Heredan los campos manuales de arriba

class GasNatural(CombustibleBase):
    class Meta: verbose_name = "Registro Gas Natural"

class CarbonMineral(CombustibleBase):
    class Meta: verbose_name = "Registro Carbón Mineral"

class FuelOil(CombustibleBase):
    class Meta: verbose_name = "Registro Fuel Oil"

class Biomasa(CombustibleBase):
    tipo = models.CharField(max_length=50, default="Genérica")
    class Meta: verbose_name = "Registro Biomasa"

class GasPropano(CombustibleBase):
    class Meta: verbose_name = "Registro GLP"