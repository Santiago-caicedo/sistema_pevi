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


# ==============================================================================
#  FORMULARIOS PANEL DE CONTROL SUPERADMIN
# ==============================================================================

from .models import CentroPevi
from web.models import Noticia


class CentroPeviForm(EstiloBootstrapMixin, forms.ModelForm):
    """Formulario completo para gestionar Centros PEVI."""

    class Meta:
        model = CentroPevi
        fields = [
            # Identificación
            'nombre', 'nombre_corto', 'codigo_interno', 'activo',
            # Branding
            'logo', 'imagen_portada', 'color_primario',
            # Ubicación
            'region', 'ciudad', 'direccion', 'latitud', 'longitud',
            # Contacto
            'email_contacto', 'telefono', 'sitio_web',
            # Redes
            'linkedin', 'twitter', 'instagram',
            # Descripción
            'descripcion', 'especialidades', 'año_vinculacion',
            # Director
            'director_nombre', 'director_cargo', 'director_foto', 'director_email',
            # Métricas
            'estudiantes_formados',
        ]
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 4}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'color_primario': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
        }


class UsuarioAdminForm(EstiloBootstrapMixin, forms.ModelForm):
    """Formulario para crear usuarios desde el Panel de Control (Superadmin)."""

    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        min_length=8
    )
    password_confirm = forms.CharField(
        label="Confirmar Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Usuario
        fields = [
            'username', 'first_name', 'last_name', 'email',
            'centro_pevi', 'rol', 'cargo',
            'is_active', 'is_staff', 'is_superuser'
        ]
        widgets = {
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_superuser': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password and password_confirm and password != password_confirm:
            raise ValidationError("Las contraseñas no coinciden.")

        return cleaned_data


class UsuarioAdminEditForm(EstiloBootstrapMixin, forms.ModelForm):
    """Formulario para editar usuarios desde el Panel de Control."""

    nueva_password = forms.CharField(
        label="Nueva Contraseña (opcional)",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False,
        min_length=8,
        help_text="Dejar vacío para mantener la contraseña actual."
    )

    class Meta:
        model = Usuario
        fields = [
            'username', 'first_name', 'last_name', 'email',
            'centro_pevi', 'rol', 'cargo',
            'is_active', 'is_staff', 'is_superuser'
        ]
        widgets = {
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_superuser': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class NoticiaAdminForm(EstiloBootstrapMixin, forms.ModelForm):
    """Formulario para gestionar Noticias."""

    class Meta:
        model = Noticia
        fields = ['titulo', 'slug', 'imagen_portada', 'resumen', 'contenido', 'publicada']
        widgets = {
            'resumen': forms.Textarea(attrs={'rows': 3}),
            'contenido': forms.Textarea(attrs={'rows': 10}),
            'publicada': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        help_texts = {
            'slug': 'URL amigable. Ej: nueva-alianza-upme',
        }