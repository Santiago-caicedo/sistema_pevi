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
            if self.creator.es_nacional:
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
            if self.creator.es_nacional:
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

        # SEGURIDAD: Usuarios que no son Director Nacional deben tener centro asignado
        rol = cleaned_data.get('rol')
        centro = cleaned_data.get('centro_pevi')
        is_superuser = cleaned_data.get('is_superuser')

        if rol != Usuario.ROL_NACIONAL and not is_superuser and not centro:
            self.add_error('centro_pevi',
                "Los usuarios con rol diferente a Director Nacional deben tener un Centro asignado.")

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

    def clean(self):
        cleaned_data = super().clean()

        # SEGURIDAD: Usuarios que no son Director Nacional deben tener centro asignado
        rol = cleaned_data.get('rol')
        centro = cleaned_data.get('centro_pevi')
        is_superuser = cleaned_data.get('is_superuser')

        if rol != Usuario.ROL_NACIONAL and not is_superuser and not centro:
            self.add_error('centro_pevi',
                "Los usuarios con rol diferente a Director Nacional deben tener un Centro asignado.")

        return cleaned_data


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


# ==============================================================================
#  FORMULARIO PÚBLICO: SOLICITUD DE USUARIO (sin login)
# ==============================================================================

from .models import SolicitudUsuario


class SolicitudUsuarioForm(EstiloBootstrapMixin, forms.ModelForm):
    """
    Formulario público para que los centros soliciten la creación de cuentas.
    Solo permite solicitar Profesor o Estudiante y exige elegir un centro activo.
    Incluye un honeypot anti-spam ('website') que debe quedar vacío.
    """

    # Honeypot: oculto vía CSS; si un bot lo llena, descartamos la solicitud.
    website = forms.CharField(
        required=False, widget=forms.TextInput(attrs={'autocomplete': 'off', 'tabindex': '-1'})
    )

    class Meta:
        model = SolicitudUsuario
        fields = ['nombres', 'apellidos', 'email', 'centro_pevi',
                  'rol_solicitado', 'cargo', 'telefono', 'justificacion']
        widgets = {
            'justificacion': forms.Textarea(attrs={'rows': 3}),
        }
        labels = {
            'centro_pevi': 'Centro PEVI al que perteneces',
            'rol_solicitado': 'Rol solicitado',
            'justificacion': 'Justificación / comentarios (opcional)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Solo centros activos
        self.fields['centro_pevi'].queryset = CentroPevi.objects.filter(activo=True).order_by('nombre')
        # Blindaje: limitar choices a Profesor/Estudiante (anti-tamper en UI)
        self.fields['rol_solicitado'].choices = SolicitudUsuario.ROLES_SOLICITABLES
        # Campos obligatorios
        for f in ['nombres', 'apellidos', 'email', 'centro_pevi', 'rol_solicitado']:
            self.fields[f].required = True

    def clean_website(self):
        # Honeypot: si viene con contenido, es spam.
        if self.cleaned_data.get('website'):
            raise ValidationError("Solicitud inválida.")
        return ''

    def clean_rol_solicitado(self):
        rol = self.cleaned_data.get('rol_solicitado')
        permitidos = [c[0] for c in SolicitudUsuario.ROLES_SOLICITABLES]
        if rol not in permitidos:
            raise ValidationError("Rol no permitido para solicitud.")
        return rol