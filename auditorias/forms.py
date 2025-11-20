from django import forms
from .models import (
    DocumentoProyecto, Empresa, ProyectoAuditoria, 
    Electricidad, GasNatural, CarbonMineral, 
    FuelOil, Biomasa, GasPropano
)

# --- MIXIN DE DISEÑO ---
class EstiloBootstrapMixin:
    """
    Mixin para aplicar clases de Bootstrap 5 a todos los campos automáticamente.
    Ahorra tener que escribir 'class': 'form-control' en cada widget.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            # Checkbox gets a specific class
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
            # Selects get form-select
            elif isinstance(field.widget, forms.Select) or isinstance(field.widget, forms.SelectMultiple):
                field.widget.attrs['class'] = 'form-select'
            # Standard inputs get form-control
            else:
                field.widget.attrs['class'] = 'form-control'
                field.widget.attrs['placeholder'] = field.label  # Placeholder automático

# --- FORMULARIOS ADMINISTRATIVOS ---

class EmpresaForm(EstiloBootstrapMixin, forms.ModelForm):
    class Meta:
        model = Empresa
        fields = '__all__'
        widgets = {
            'direccion': forms.Textarea(attrs={'rows': 2}),
        }

class ProyectoForm(EstiloBootstrapMixin, forms.ModelForm):
    class Meta:
        model = ProyectoAuditoria
        fields = [
            'nombre_proyecto', 'empresa', 'fecha_inicio', 'fecha_cierre_estimada', 
             'lider_proyecto', 'equipo',
        ]
        widgets = {
            'fecha_inicio': forms.DateInput(attrs={'type': 'date'}),
            'fecha_cierre_estimada': forms.DateInput(attrs={'type': 'date'}),
            'equipo': forms.SelectMultiple(attrs={'size': '5'}), # Lista múltiple más alta
        }
    
    def __init__(self, *args, **kwargs):
        # Extraemos el usuario para filtrar las empresas de SU centro
        user = kwargs.pop('user', None) 
        super().__init__(*args, **kwargs)
        
        if user and user.centro_pevi:
            # Solo mostrar empresas que ya han sido auditadas por ESTE centro
            # O todas si es la primera vez (ajusta esta lógica según prefieras)
            # Por ahora mostramos todas las empresas registradas para simplificar
            pass 
            # Si quisieras filtrar:
            # self.fields['empresa'].queryset = Empresa.objects.filter(...)

# --- FORMULARIOS DE REGISTRO DE ENERGÍA (BITÁCORA MANUAL) ---

class RegistroEnergiaForm(EstiloBootstrapMixin, forms.ModelForm):
    """
    Clase base para todos los energéticos.
    Asegura que los campos numéricos acepten decimales.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Permitir decimales en todos los campos numéricos
        for field in self.fields.values():
            if isinstance(field.widget, forms.NumberInput):
                field.widget.attrs['step'] = 'any'

class ElectricidadForm(RegistroEnergiaForm):
    class Meta:
        model = Electricidad
        exclude = ['proyecto']
        labels = {
            'consumo_mensual': 'Consumo Mensual (kWh/mes)',
            'consumo_anual': 'Consumo Anual (kWh/año)',
            'costo_unitario': 'Costo Unitario (COP/kWh)',
            'factor_emision': 'Factor de Emisión (kgCO2/kWh)',
        }

class GasNaturalForm(RegistroEnergiaForm):
    class Meta:
        model = GasNatural
        exclude = ['proyecto']
        labels = {
            'consumo_mensual_orig': 'Consumo Mensual (m³/mes)',
            'consumo_anual_orig': 'Consumo Anual (m³/año)',
            'costo_unitario': 'Costo Unitario (COP/m³)',
            'unidad_pc': 'Unidad del Poder Calorífico (Ej: kWh/m³)',
            'factor_emision': 'Factor de Emisión (kgCO2/m³)',
        }

class CarbonForm(RegistroEnergiaForm):
    class Meta:
        model = CarbonMineral
        exclude = ['proyecto']
        labels = {
            'consumo_mensual_orig': 'Consumo Mensual (Ton/mes)',
            'consumo_anual_orig': 'Consumo Anual (Ton/año)',
            'costo_unitario': 'Costo Unitario (COP/Ton)',
            'unidad_pc': 'Unidad del Poder Calorífico (Ej: MJ/kg)',
            'factor_emision': 'Factor de Emisión (kgCO2/Ton)',
        }

class FuelOilForm(RegistroEnergiaForm):
    class Meta:
        model = FuelOil
        exclude = ['proyecto']
        labels = {
            'consumo_mensual_orig': 'Consumo Mensual (Galones/mes)',
            'consumo_anual_orig': 'Consumo Anual (Galones/año)',
            'costo_unitario': 'Costo Unitario (COP/Galón)',
            'unidad_pc': 'Unidad del Poder Calorífico (Ej: MJ/Gal)',
            'factor_emision': 'Factor de Emisión (kgCO2/Gal)',
        }

class BiomasaForm(RegistroEnergiaForm):
    class Meta:
        model = Biomasa
        exclude = ['proyecto']
        labels = {
            'tipo': 'Tipo de Biomasa (Ej: Bagazo, Cisco)',
            'consumo_mensual_orig': 'Consumo Mensual (Ton/mes)',
            'consumo_anual_orig': 'Consumo Anual (Ton/año)',
            'costo_unitario': 'Costo Unitario (COP/Ton)',
            'unidad_pc': 'Unidad del Poder Calorífico (Ej: kJ/kg)',
            'factor_emision': 'Factor de Emisión (kgCO2/Ton)',
        }

class GasPropanoForm(RegistroEnergiaForm):
    class Meta:
        model = GasPropano
        exclude = ['proyecto']
        labels = {
            'consumo_mensual_orig': 'Consumo Mensual (kg/mes)',
            'consumo_anual_orig': 'Consumo Anual (kg/año)',
            'costo_unitario': 'Costo Unitario (COP/kg)',
            'unidad_pc': 'Unidad del Poder Calorífico',
            'factor_emision': 'Factor de Emisión (kgCO2/kg)',
        }

class ProduccionForm(EstiloBootstrapMixin, forms.ModelForm):
    class Meta:
        model = ProyectoAuditoria
        fields = ['produccion_total', 'unidad_produccion']
        labels = {
            'produccion_total': 'Cantidad Producida (Año Base)',
            'unidad_produccion': 'Unidad de Medida (Ej: Ton, Unidades)'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Forzamos step any para decimales
        self.fields['produccion_total'].widget.attrs['step'] = 'any'


class DocumentoForm(EstiloBootstrapMixin, forms.ModelForm):
    class Meta:
        model = DocumentoProyecto
        fields = ['descripcion', 'archivo']
        labels = {
            'descripcion': 'Nombre del Archivo / Descripción',
            'archivo': 'Seleccionar Archivo'
        }