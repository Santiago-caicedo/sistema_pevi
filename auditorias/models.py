from django.db import models
from django.conf import settings # Para referenciar al Usuario correctamente
from gestion.models import CentroPevi
from django.core.validators import FileExtensionValidator

class Empresa(models.Model):
    """
    Información estática de la empresa cliente.
    AISLAMIENTO: Cada empresa pertenece a un centro específico.
    """
    # Relación con Centro (AISLAMIENTO DE DATOS)
    centro = models.ForeignKey(
        CentroPevi,
        on_delete=models.PROTECT,
        related_name="empresas",
        verbose_name="Centro PEVI",
        null=True,  # Temporalmente null para migración de datos existentes
        blank=True
    )

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

    FASES = [
        ('FASE_1', 'Fase 1'),
        ('FASE_2', 'Fase 2'),
        ('FASE_3', 'Fase 3'),
        ('FASE_4', 'Fase 4'),
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
    fase = models.CharField(
        max_length=10,
        choices=FASES,
        null=True,
        blank=True,
        verbose_name="Fase del Programa"
    )

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
    
    def get_total_kwh(self):
        """
        Calcula la suma total de energía (Eléctrica + Térmica) en kWh.
        Usado para KPIs rápidos en listados y dashboards.
        """
        total = 0.0
        
        # 1. Sumar Electricidad
        # Usamos .first() porque la relación devuelve un QuerySet
        elec = self.electricidad_related.first()
        if elec:
            total += elec.consumo_anual

        # 2. Sumar Combustibles (Usando el campo normalizado en kWh)
        # Lista de las relaciones inversas (related_name)
        combustibles = [
            self.gasnatural_related.first(),
            self.carbonmineral_related.first(),
            self.fueloil_related.first(),
            self.biomasa_related.first(),
            self.gaspropano_related.first()
        ]

        for fuente in combustibles:
            if fuente:
                # Sumamos el campo 'consumo_anual_kwh' que calculamos en el save()
                total += fuente.consumo_anual_kwh
        
        return total
    
    def get_total_emisiones(self):
        """Calcula la Huella de Carbono Total del proyecto."""
        total = 0.0
        # Lista de relaciones
        fuentes = [
            self.electricidad_related.first(),
            self.gasnatural_related.first(),
            self.carbonmineral_related.first(),
            self.fueloil_related.first(),
            self.biomasa_related.first(),
            self.gaspropano_related.first()
        ]
        for f in fuentes:
            if f: total += f.emisiones_totales
        return total

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

    # --- 3. OPORTUNIDADES DE MEJORA ---
    porcentaje_reduccion = models.FloatField(
        verbose_name="Meta de Reducción (%)",
        default=0,
        help_text="Porcentaje de reducción objetivo para este energético"
    )

    class Meta:
        abstract = True

    def get_ahorro_energia_potencial(self):
        """Calcula el ahorro potencial en kWh basado en el % de reducción."""
        kwh = getattr(self, 'consumo_anual', None) or getattr(self, 'consumo_anual_kwh', 0)
        return (kwh * self.porcentaje_reduccion) / 100 if self.porcentaje_reduccion else 0

    def get_ahorro_costo_potencial(self):
        """Calcula el ahorro potencial en COP basado en el % de reducción."""
        return (self.costo_total_anual * self.porcentaje_reduccion) / 100 if self.porcentaje_reduccion else 0

    def get_ahorro_emisiones_potencial(self):
        """Calcula la reducción de emisiones potencial en TonCO2."""
        return (self.emisiones_totales * self.porcentaje_reduccion) / 100 if self.porcentaje_reduccion else 0

class Electricidad(FuenteEnergiaBase):
    """ Campos específicos del Excel para Electricidad """
    consumo_mensual = models.FloatField(verbose_name="Consumo Mensual (kWh/mes)")
    consumo_anual = models.FloatField(verbose_name="Consumo Anual (kWh/año)")

    # La electricidad no tiene conversión de unidades ni PC complejo

    def get_kwh_equivalente(self):
        return self.consumo_anual # Ya viene en kWh

    def calcular_emisiones_ton_co2(self):
        return self.emisiones_totales

    def save(self, *args, **kwargs):
        # AUTO-CÁLCULO DE EMISIONES: (consumo_anual × factor_emision) / 1000
        if self.consumo_anual and self.factor_emision:
            self.emisiones_totales = (self.consumo_anual * self.factor_emision) / 1000
        super().save(*args, **kwargs)

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
    poder_calorifico = models.FloatField(verbose_name="Poder Calorífico (PC)")
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
        # Fórmula: Energía (kJ) = Cantidad × FactorUnidad × PC × FactorEnergia
        # Energía (kWh) = Energía (kJ) / 3600

        factor_unidad = 1.0    # Conversión de unidad de consumo
        factor_energia = 1.0   # Conversión de MJ a kJ (si PC está en MJ)

        if self._meta.model_name == 'carbonmineral':
            # Carbón: Ton → kg, PC en MJ/kg
            factor_unidad = 1000.0
            factor_energia = 1000.0
        elif self._meta.model_name == 'biomasa':
            # Biomasa: Ton → kg, PC en kJ/kg
            factor_unidad = 1000.0
            factor_energia = 1.0
        elif self._meta.model_name == 'fueloil':
            # Fuel Oil: Galones (sin conversión), PC en MJ/usgal
            factor_unidad = 1.0
            factor_energia = 1000.0
        elif self._meta.model_name == 'gaspropano':
            # GLP: kg (sin conversión), PC en MJ/kg
            factor_unidad = 1.0
            factor_energia = 1000.0
        # Gas Natural: m³ (sin conversión), PC en kJ/m³ → factores = 1.0

        if self.consumo_anual_orig and self.poder_calorifico:
            # 1. Calculamos energía total en kJ
            energia_kj = (self.consumo_anual_orig * factor_unidad) * self.poder_calorifico * factor_energia

            # 2. Convertimos a kWh (1 kWh = 3600 kJ)
            self.consumo_anual_kwh = energia_kj / 3600

            # 3. Calculamos indicador de costo
            if self.costo_total_anual and self.consumo_anual_kwh > 0:
                self.costo_kwh_equivalente = self.costo_total_anual / self.consumo_anual_kwh

        # AUTO-CÁLCULO DE EMISIONES: (consumo_anual_orig × factor_emision) / 1000
        if self.consumo_anual_orig and self.factor_emision:
            self.emisiones_totales = (self.consumo_anual_orig * self.factor_emision) / 1000

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