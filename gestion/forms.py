from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Usuario

class EstiloBootstrapMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = 'form-select'
            else:
                field.widget.attrs['class'] = 'form-control'

class UsuarioForm(EstiloBootstrapMixin, UserCreationForm):
    """Formulario para crear usuarios con contraseña."""
    class Meta:
        model = Usuario
        fields = ['username', 'first_name', 'last_name', 'email', 'rol', 'cargo']
        # Nota: 'password' lo agrega automáticamente UserCreationForm

class UsuarioEditarForm(EstiloBootstrapMixin, forms.ModelForm):
    """Formulario para editar datos (sin tocar la contraseña)."""
    class Meta:
        model = Usuario
        fields = ['first_name', 'last_name', 'email', 'rol', 'cargo', 'is_active']
        labels = {'is_active': 'Usuario Activo (Permitir acceso)'}
        widgets = {
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }