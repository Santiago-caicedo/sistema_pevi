from django import forms
from .models import (
    Empresa, ProyectoAuditoria, DocumentoProyecto,
    Electricidad, GasNatural, CarbonMineral, 
    FuelOil, Biomasa, GasPropano
)

# --- MIXIN DE DISEÑO ---
class EstiloBootstrapMixin:
    """
    Mixin para aplicar clases de Bootstrap 5 a todos los campos.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
            elif isinstance(field.widget, forms.Select) or isinstance(field.widget, forms.SelectMultiple):
                field.widget.attrs['class'] = 'form-select'
            else:
                field.widget.attrs['class'] = 'form-control'
                field.widget.attrs['placeholder'] = field.label

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
            'lider_proyecto', 'equipo'
        ]
        widgets = {
            'fecha_inicio': forms.DateInput(attrs={'type': 'date'}),
            'fecha_cierre_estimada': forms.DateInput(attrs={'type': 'date'}),
            'equipo': forms.SelectMultiple(attrs={'size': '5'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None) 
        super().__init__(*args, **kwargs)
        if user and user.centro_pevi:
            # Aquí podrías filtrar queryset si fuera necesario
            pass 

class ProduccionForm(EstiloBootstrapMixin, forms.ModelForm):
    class Meta:
        model = ProyectoAuditoria
        fields = ['produccion_total', 'unidad_produccion']
        labels = {
            'produccion_total': 'Cantidad Producida (Año Base)',
            'unidad_produccion': 'Unidad de Medida (Ej: Ton, Unidades)'
        }
    
    def __init__(self, *args, **kwargs):
        # -----------------------------------------------------------
        # CORRECCIÓN: INTERCEPTOR DE COMAS
        # Limpiamos 'produccion_total' antes de que Django lo lea
        # -----------------------------------------------------------
        if args:
            data = args[0].copy()
            if 'produccion_total' in data and isinstance(data['produccion_total'], str):
                data['produccion_total'] = data['produccion_total'].replace(',', '')
            args = (data,) + args[1:]
            
        super().__init__(*args, **kwargs)
        
        # Forzar que el input sea Texto para que el navegador no moleste con validaciones HTML5
        self.fields['produccion_total'].widget = forms.TextInput(attrs={
            'class': 'form-control', 
            'autocomplete': 'off'
        })

class DocumentoForm(EstiloBootstrapMixin, forms.ModelForm):
    class Meta:
        model = DocumentoProyecto
        fields = ['descripcion', 'archivo']
        labels = {
            'descripcion': 'Nombre del Archivo / Descripción',
            'archivo': 'Seleccionar Archivo'
        }

# --- FORMULARIOS DE REGISTRO DE ENERGÍA (BITÁCORA MANUAL) ---

class RegistroEnergiaForm(EstiloBootstrapMixin, forms.ModelForm):
    """
    Clase base inteligente.
    1. Intercepta los datos para quitar comas.
    2. Convierte los inputs numéricos a texto para permitir formato visual.
    """
    def __init__(self, *args, **kwargs):
        # -----------------------------------------------------------
        # CORRECCIÓN DEL ERROR "ENTER A NUMBER":
        # Interceptamos los datos (args[0]) antes de que el formulario los procese.
        # Si encontramos comas en campos numéricos, las quitamos aquí.
        # -----------------------------------------------------------
        if args:
            data = args[0].copy() # Hacemos una copia mutable de los datos POST
            for key, value in data.items():
                # Lista de campos que sabemos que son números
                palabras_clave = ['consumo', 'costo', 'poder', 'emisiones', 'factor', 'kwh']
                
                # Si el campo contiene alguna palabra clave y el valor es texto con coma
                if any(x in key for x in palabras_clave) and isinstance(value, str):
                    # Quitamos la coma para que Django reciba "1200.50" en vez de "1,200.50"
                    data[key] = value.replace(',', '')
            
            # Reempaquetamos los datos limpios
            args = (data,) + args[1:]
        
        super().__init__(*args, **kwargs)

        # Configuración de Widgets: Forzamos TextInput para que el navegador
        # no intente validar números y nos deje poner comas visualmente.
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.NumberInput):
                field.widget = forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'})

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
            'consumo_mensual_orig': 'Consumo Mensual (m³)',
            'consumo_anual_orig': 'Consumo Anual (m³)',
            'costo_unitario': 'Costo Unitario (COP/m³)',
            'unidad_pc': 'Unidad PC',
            'factor_emision': 'Factor de Emisión',
            'consumo_mensual_kwh': 'Consumo Eq. Mensual (kWh)',
            'consumo_anual_kwh': 'Consumo Eq. Anual (kWh)',
            'costo_kwh_equivalente': 'Costo Equivalente ($/kWh)',
        }

class CarbonForm(RegistroEnergiaForm):
    class Meta:
        model = CarbonMineral
        exclude = ['proyecto']
        labels = {
            'consumo_mensual_orig': 'Consumo Mensual (Ton)',
            'consumo_anual_orig': 'Consumo Anual (Ton)',
            'costo_unitario': 'Costo Unitario (COP/Ton)',
            'unidad_pc': 'Unidad PC',
            'factor_emision': 'Factor de Emisión',
            'consumo_mensual_kwh': 'Consumo Eq. Mensual (kWh)',
            'consumo_anual_kwh': 'Consumo Eq. Anual (kWh)',
            'costo_kwh_equivalente': 'Costo Equivalente ($/kWh)',
        }

class FuelOilForm(RegistroEnergiaForm):
    class Meta:
        model = FuelOil
        exclude = ['proyecto']
        labels = {
            'consumo_mensual_orig': 'Consumo Mensual (Gal)',
            'consumo_anual_orig': 'Consumo Anual (Gal)',
            'costo_unitario': 'Costo Unitario (COP/Gal)',
            'unidad_pc': 'Unidad PC',
            'factor_emision': 'Factor de Emisión',
            'consumo_mensual_kwh': 'Consumo Eq. Mensual (kWh)',
            'consumo_anual_kwh': 'Consumo Eq. Anual (kWh)',
            'costo_kwh_equivalente': 'Costo Equivalente ($/kWh)',
        }

class BiomasaForm(RegistroEnergiaForm):
    class Meta:
        model = Biomasa
        exclude = ['proyecto']
        labels = {
            'tipo': 'Tipo de Biomasa',
            'consumo_mensual_orig': 'Consumo Mensual (Ton)',
            'consumo_anual_orig': 'Consumo Anual (Ton)',
            'costo_unitario': 'Costo Unitario (COP/Ton)',
            'unidad_pc': 'Unidad PC',
            'factor_emision': 'Factor de Emisión',
            'consumo_mensual_kwh': 'Consumo Eq. Mensual (kWh)',
            'consumo_anual_kwh': 'Consumo Eq. Anual (kWh)',
            'costo_kwh_equivalente': 'Costo Equivalente ($/kWh)',
        }

class GasPropanoForm(RegistroEnergiaForm):
    class Meta:
        model = GasPropano
        exclude = ['proyecto']
        labels = {
            'consumo_mensual_orig': 'Consumo Mensual (kg)',
            'consumo_anual_orig': 'Consumo Anual (kg)',
            'costo_unitario': 'Costo Unitario (COP/kg)',
            'unidad_pc': 'Unidad PC',
            'factor_emision': 'Factor de Emisión',
            'consumo_mensual_kwh': 'Consumo Eq. Mensual (kWh)',
            'consumo_anual_kwh': 'Consumo Eq. Anual (kWh)',
            'costo_kwh_equivalente': 'Costo Equivalente ($/kWh)',
        }