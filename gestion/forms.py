from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import Usuario

class EstiloBootstrapMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = 'form-select'
            else:
                field.widget.attrs['class'] = 'form-control'

class UsuarioForm(EstiloBootstrapMixin, UserCreationForm):
    """Formulario para crear usuarios (Incluye password)."""
    
    class Meta:
        model = Usuario
        # IMPORTANTE: Al listar explícitamente los campos, Django IGNORA cualquier otro dato
        # que envíen por POST (como is_superuser o is_staff). ¡Esto evita la inyección!
        fields = ['username', 'first_name', 'last_name', 'email', 'rol', 'cargo']

    def __init__(self, *args, **kwargs):
        # Extraemos el usuario que está intentando crear al nuevo
        self.creator = kwargs.pop('creator', None)
        super().__init__(*args, **kwargs)
        
        # LÓGICA DE JERARQUÍA DE ROLES
        if self.creator:
            if self.creator.is_superuser or self.creator.rol == Usuario.ROL_NACIONAL:
                # Dios o Nacional: Pueden crear CUALQUIER rol
                pass 
            elif self.creator.rol == Usuario.ROL_DIRECTOR:
                # Director de Centro: SOLO puede crear Profesores o Estudiantes
                self.fields['rol'].choices = [
                    (Usuario.ROL_PROFESOR, 'Profesor Líder de Proyecto'),
                    (Usuario.ROL_ESTUDIANTE, 'Estudiante / Ingeniero Junior'),
                ]
            else:
                # Si un estudiante hackea y llega aquí, le quitamos todas las opciones
                self.fields['rol'].choices = []

    def clean_rol(self):
        """Validación final anti-hackeo."""
        rol = self.cleaned_data.get('rol')
        
        # Si un Director intenta inyectar 'DIRECTOR_NACIONAL' por POST, esto lo detiene
        if self.creator and self.creator.rol == Usuario.ROL_DIRECTOR:
            if rol not in [Usuario.ROL_PROFESOR, Usuario.ROL_ESTUDIANTE]:
                raise ValidationError("No tienes permisos para asignar este rol superior.")
        
        return rol


class UsuarioEditarForm(EstiloBootstrapMixin, forms.ModelForm):
    """Formulario para editar (Sin password)."""
    
    class Meta:
        model = Usuario
        fields = ['first_name', 'last_name', 'email', 'rol', 'cargo', 'is_active']
        widgets = {
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }

    def __init__(self, *args, **kwargs):
        self.creator = kwargs.pop('creator', None)
        super().__init__(*args, **kwargs)
        
        # Misma lógica de restricción que al crear
        if self.creator:
            if self.creator.is_superuser or self.creator.rol == Usuario.ROL_NACIONAL:
                pass
            elif self.creator.rol == Usuario.ROL_DIRECTOR:
                self.fields['rol'].choices = [
                    (Usuario.ROL_PROFESOR, 'Profesor Líder de Proyecto'),
                    (Usuario.ROL_ESTUDIANTE, 'Estudiante / Ingeniero Junior'),
                ]
                
                # Proteger el campo 'is_active' si quieres que solo admins desactiven (opcional)
                # self.fields['is_active'].disabled = True 

    def clean_rol(self):
        rol = self.cleaned_data.get('rol')
        if self.creator and self.creator.rol == Usuario.ROL_DIRECTOR:
            if rol not in [Usuario.ROL_PROFESOR, Usuario.ROL_ESTUDIANTE]:
                raise ValidationError("Intento de escalada de privilegios bloqueado.")
        return rol