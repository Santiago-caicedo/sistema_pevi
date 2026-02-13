from django import forms
from .models import (
    Empresa, ProyectoAuditoria, DocumentoProyecto,
    Electricidad, GasNatural, CarbonMineral,
    FuelOil, Biomasa, GasPropano, OportunidadMejora
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
        # SEGURIDAD: Lista explícita de campos permitidos (NO usar __all__)
        fields = [
            'centro',
            'razon_social', 'nit', 'sector_productivo',
            'direccion', 'ciudad',
            'contacto_nombre', 'contacto_email', 'contacto_telefono'
        ]
        widgets = {
            'direccion': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self._user = user  # Guardar para validación

        if user:
            if user.is_superuser or user.rol == 'DIRECTOR_NACIONAL':
                # Superadmin/Nacional: Mostrar selector de centro (obligatorio)
                from gestion.models import CentroPevi
                self.fields['centro'].queryset = CentroPevi.objects.filter(activo=True)
                self.fields['centro'].required = True
            elif user.centro_pevi:
                # Director de Centro: Ocultar campo, se asigna automáticamente
                self.fields['centro'].widget = forms.HiddenInput()
                self.fields['centro'].initial = user.centro_pevi
                self.fields['centro'].required = False

    def clean_centro(self):
        """Garantiza que toda empresa tenga un centro asignado."""
        centro = self.cleaned_data.get('centro')

        # Si no viene centro del formulario, usar el del usuario
        if not centro and hasattr(self, '_user') and self._user and self._user.centro_pevi:
            return self._user.centro_pevi

        if not centro:
            raise forms.ValidationError("Debe asignar un Centro PEVI a la empresa.")

        return centro

class ProyectoForm(EstiloBootstrapMixin, forms.ModelForm):
    class Meta:
        model = ProyectoAuditoria
        fields = [
            'nombre_proyecto', 'empresa', 'fase', 'fecha_inicio', 'fecha_cierre_estimada',
            'lider_proyecto', 'equipo'
        ]
        widgets = {
            'fecha_inicio': forms.DateInput(attrs={'type': 'date'}),
            'fecha_cierre_estimada': forms.DateInput(attrs={'type': 'date'}),
            'equipo': forms.SelectMultiple(attrs={'size': '5'}),
        }
        labels = {
            'fase': 'Fase del Programa (Opcional)',
        }

    def __init__(self, *args, **kwargs):
        from gestion.models import Usuario
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self._user = user  # Guardar para validación

        # AISLAMIENTO DE CENTROS: Filtrar todo por centro del usuario
        if user:
            if user.is_superuser or user.rol == 'DIRECTOR_NACIONAL':
                # Nacional ve todo (para casos excepcionales de asignación)
                pass
            elif user.centro_pevi:
                # Director Centro y Profesor: Solo ven recursos de su centro

                # Filtrar empresas por centro
                self.fields['empresa'].queryset = Empresa.objects.filter(
                    centro=user.centro_pevi
                )

                # Filtrar líderes por centro
                self.fields['lider_proyecto'].queryset = Usuario.objects.filter(
                    centro_pevi=user.centro_pevi,
                    rol__in=['PROFESOR', 'DIRECTOR_CENTRO', 'DIRECTOR_NACIONAL']
                )

                # Filtrar equipo por centro
                self.fields['equipo'].queryset = Usuario.objects.filter(
                    centro_pevi=user.centro_pevi
                )

    def clean(self):
        """Valida consistencia de centro entre empresa, líder y equipo."""
        cleaned_data = super().clean()
        empresa = cleaned_data.get('empresa')
        lider = cleaned_data.get('lider_proyecto')
        equipo = cleaned_data.get('equipo')

        # Solo validar para Nacional/Superuser (los demás ya están filtrados)
        if hasattr(self, '_user') and self._user:
            if self._user.is_superuser or self._user.rol == 'DIRECTOR_NACIONAL':
                if empresa:
                    centro_empresa = empresa.centro

                    # Validar que el líder sea del mismo centro que la empresa
                    if lider and lider.centro_pevi and centro_empresa:
                        if lider.centro_pevi != centro_empresa:
                            self.add_error('lider_proyecto',
                                f"El líder pertenece a {lider.centro_pevi.nombre_corto or lider.centro_pevi.nombre}, "
                                f"pero la empresa es de {centro_empresa.nombre_corto or centro_empresa.nombre}.")

                    # Validar que el equipo sea del mismo centro que la empresa
                    if equipo and centro_empresa:
                        for miembro in equipo:
                            if miembro.centro_pevi and miembro.centro_pevi != centro_empresa:
                                self.add_error('equipo',
                                    f"{miembro.get_full_name()} pertenece a otro centro.")
                                break

        return cleaned_data 

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
        exclude = ['proyecto', 'porcentaje_reduccion']
        labels = {
            'consumo_mensual': 'Consumo Mensual (kWh/mes)',
            'consumo_anual': 'Consumo Anual (kWh/año)',
            'costo_unitario': 'Costo Unitario (COP/kWh)',
            'factor_emision': 'Factor de Emisión (kgCO2/kWh)',
        }

class GasNaturalForm(RegistroEnergiaForm):
    class Meta:
        model = GasNatural
        exclude = ['proyecto', 'porcentaje_reduccion']
        labels = {
            'consumo_mensual_orig': 'Consumo Mensual (m³)',
            'consumo_anual_orig': 'Consumo Anual (m³)',
            'costo_unitario': 'Costo Unitario (COP/m³)',
            'poder_calorifico': 'Poder Calorífico (kJ/m³)',
            'unidad_pc': 'Unidad PC',
            'factor_emision': 'Factor de Emisión (kgCO2/m³)',
            'consumo_mensual_kwh': 'Consumo Eq. Mensual (kWh)',
            'consumo_anual_kwh': 'Consumo Eq. Anual (kWh)',
            'costo_kwh_equivalente': 'Costo Equivalente ($/kWh)',
        }

class CarbonForm(RegistroEnergiaForm):
    class Meta:
        model = CarbonMineral
        exclude = ['proyecto', 'porcentaje_reduccion']
        labels = {
            'consumo_mensual_orig': 'Consumo Mensual (Ton)',
            'consumo_anual_orig': 'Consumo Anual (Ton)',
            'costo_unitario': 'Costo Unitario (COP/Ton)',
            'poder_calorifico': 'Poder Calorífico (MJ/kg)',
            'unidad_pc': 'Unidad PC',
            'factor_emision': 'Factor de Emisión (kgCO2/Ton)',
            'consumo_mensual_kwh': 'Consumo Eq. Mensual (kWh)',
            'consumo_anual_kwh': 'Consumo Eq. Anual (kWh)',
            'costo_kwh_equivalente': 'Costo Equivalente ($/kWh)',
        }

class FuelOilForm(RegistroEnergiaForm):
    class Meta:
        model = FuelOil
        exclude = ['proyecto', 'porcentaje_reduccion']
        labels = {
            'consumo_mensual_orig': 'Consumo Mensual (Gal)',
            'consumo_anual_orig': 'Consumo Anual (Gal)',
            'costo_unitario': 'Costo Unitario (COP/Gal)',
            'poder_calorifico': 'Poder Calorífico (MJ/usgal)',
            'unidad_pc': 'Unidad PC',
            'factor_emision': 'Factor de Emisión (kgCO2/Gal)',
            'consumo_mensual_kwh': 'Consumo Eq. Mensual (kWh)',
            'consumo_anual_kwh': 'Consumo Eq. Anual (kWh)',
            'costo_kwh_equivalente': 'Costo Equivalente ($/kWh)',
        }

class BiomasaForm(RegistroEnergiaForm):
    class Meta:
        model = Biomasa
        exclude = ['proyecto', 'porcentaje_reduccion']
        labels = {
            'tipo': 'Tipo de Biomasa',
            'consumo_mensual_orig': 'Consumo Mensual (Ton)',
            'consumo_anual_orig': 'Consumo Anual (Ton)',
            'costo_unitario': 'Costo Unitario (COP/Ton)',
            'poder_calorifico': 'Poder Calorífico (kJ/kg)',
            'unidad_pc': 'Unidad PC',
            'factor_emision': 'Factor de Emisión (kgCO2/Ton)',
            'consumo_mensual_kwh': 'Consumo Eq. Mensual (kWh)',
            'consumo_anual_kwh': 'Consumo Eq. Anual (kWh)',
            'costo_kwh_equivalente': 'Costo Equivalente ($/kWh)',
        }

class GasPropanoForm(RegistroEnergiaForm):
    class Meta:
        model = GasPropano
        exclude = ['proyecto', 'porcentaje_reduccion']
        labels = {
            'consumo_mensual_orig': 'Consumo Mensual (kg)',
            'consumo_anual_orig': 'Consumo Anual (kg)',
            'costo_unitario': 'Costo Unitario (COP/kg)',
            'poder_calorifico': 'Poder Calorífico (MJ/kg)',
            'unidad_pc': 'Unidad PC',
            'factor_emision': 'Factor de Emisión (kgCO2/kg)',
            'consumo_mensual_kwh': 'Consumo Eq. Mensual (kWh)',
            'consumo_anual_kwh': 'Consumo Eq. Anual (kWh)',
            'costo_kwh_equivalente': 'Costo Equivalente ($/kWh)',
        }


class OportunidadMejoraForm(EstiloBootstrapMixin, forms.ModelForm):
    class Meta:
        model = OportunidadMejora
        exclude = ['proyecto', 'created_at']
        widgets = {
            'observaciones': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        # Interceptar comas en TODOS los campos numéricos del POST
        if args:
            data = args[0].copy()
            campos_numericos = [
                'ahorro_energia', 'costos_evitados', 'emisiones_evitadas',
                'inversion', 'vpn', 'tir', 'payback'
            ]
            for key in campos_numericos:
                if key in data and isinstance(data[key], str):
                    data[key] = data[key].replace(',', '')
            args = (data,) + args[1:]

        super().__init__(*args, **kwargs)

        # Convertir campos numéricos a TextInput para evitar validación HTML5
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.NumberInput):
                field.widget = forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'})