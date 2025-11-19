from django import forms
from .models import Empresa, ProyectoAuditoria

class EstiloBootstrapMixin:
    """Mixin para aplicar clases de Bootstrap a todos los campos automáticamente"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            # Mantenemos los checkbox pequeños, el resto form-control
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
            else:
                field.widget.attrs['class'] = 'form-control'

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
        fields = ['nombre_proyecto', 'empresa', 'fecha_inicio', 'fecha_cierre_estimada', 
                  'produccion_total', 'unidad_produccion', 'lider_proyecto', 'equipo']
        widgets = {
            'fecha_inicio': forms.DateInput(attrs={'type': 'date'}),
            'fecha_cierre_estimada': forms.DateInput(attrs={'type': 'date'}),
            'equipo': forms.SelectMultiple(attrs={'class': 'form-select', 'size': '5'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None) # Recibimos el usuario logueado
        super().__init__(*args, **kwargs)
        
        # FILTRADO INTELIGENTE:
        # Si el usuario es de la "Universidad A", solo debe ver empresas y usuarios de la "Universidad A".
        if user and user.centro_pevi:
            self.fields['empresa'].queryset = Empresa.objects.filter(auditorias__centro=user.centro_pevi).distinct()
            # Aquí podrías filtrar también los usuarios del equipo para que sean solo de su centro