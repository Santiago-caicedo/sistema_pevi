from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, CentroPevi, RegistroActividad

# 1. Registrar Centro PEVI
@admin.register(CentroPevi)
class CentroPeviAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'nombre_corto', 'ciudad', 'region', 'año_vinculacion', 'proyectos_count', 'activo')
    search_fields = ('nombre', 'nombre_corto', 'codigo_interno', 'ciudad')
    list_filter = ('region', 'activo', 'año_vinculacion')
    list_editable = ('activo',)
    ordering = ['nombre']

    fieldsets = (
        ('Identificación', {
            'fields': ('nombre', 'nombre_corto', 'codigo_interno', 'activo')
        }),
        ('Branding / Imagen', {
            'fields': ('logo', 'imagen_portada', 'color_primario'),
            'classes': ('collapse',)
        }),
        ('Ubicación', {
            'fields': ('region', 'ciudad', 'direccion', ('latitud', 'longitud')),
        }),
        ('Contacto', {
            'fields': ('email_contacto', 'telefono', 'sitio_web'),
        }),
        ('Redes Sociales', {
            'fields': ('linkedin', 'twitter', 'instagram'),
            'classes': ('collapse',)
        }),
        ('Descripción y Capacidades', {
            'fields': ('descripcion', 'especialidades', 'año_vinculacion'),
        }),
        ('Equipo Directivo', {
            'fields': ('director_nombre', 'director_cargo', 'director_foto', 'director_email'),
            'classes': ('collapse',)
        }),
        ('Métricas', {
            'fields': ('estudiantes_formados',),
            'classes': ('collapse',)
        }),
    )

    def proyectos_count(self, obj):
        return obj.proyectos_count
    proyectos_count.short_description = 'Proyectos'

# 2. Registrar el Usuario Personalizado
# Usamos UserAdmin para mantener la seguridad de contraseñas de Django
@admin.register(Usuario)
class CustomUserAdmin(UserAdmin):
    # Qué columnas ver en la lista de usuarios
    list_display = ('username', 'email', 'get_nombre_completo', 'rol', 'centro_pevi', 'is_active')
    list_filter = ('rol', 'centro_pevi', 'is_staff')
    
    # Agregamos nuestros campos personalizados al formulario de EDICIÓN de usuario
    fieldsets = UserAdmin.fieldsets + (
        ('Información PEVI', {'fields': ('centro_pevi', 'rol', 'cargo')}),
    )
    
    # Agregamos nuestros campos al formulario de CREACIÓN de usuario
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Información PEVI', {'fields': ('centro_pevi', 'rol', 'cargo')}),
    )

    def get_nombre_completo(self, obj):
        return obj.get_full_name()
    get_nombre_completo.short_description = 'Nombre'


# 3. Registro de Actividad (Logs)
@admin.register(RegistroActividad)
class RegistroActividadAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'tipo', 'accion', 'usuario', 'modelo_afectado', 'objeto_repr', 'ip_address')
    list_filter = ('tipo', 'accion', 'modelo_afectado', 'centro', 'timestamp')
    search_fields = ('usuario__username', 'objeto_repr', 'descripcion', 'ip_address', 'username_intento')
    date_hierarchy = 'timestamp'
    readonly_fields = (
        'tipo', 'accion', 'timestamp', 'usuario', 'username_intento',
        'modelo_afectado', 'objeto_id', 'objeto_repr', 'descripcion',
        'ip_address', 'user_agent', 'centro'
    )
    ordering = ['-timestamp']

    fieldsets = (
        ('Evento', {
            'fields': ('tipo', 'accion', 'timestamp')
        }),
        ('Usuario', {
            'fields': ('usuario', 'username_intento', 'centro')
        }),
        ('Objeto Afectado', {
            'fields': ('modelo_afectado', 'objeto_id', 'objeto_repr')
        }),
        ('Detalles', {
            'fields': ('descripcion', 'ip_address', 'user_agent')
        }),
    )

    def has_add_permission(self, request):
        """No permitir crear logs manualmente."""
        return False

    def has_change_permission(self, request, obj=None):
        """No permitir editar logs."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Solo superusuarios pueden eliminar logs."""
        return request.user.is_superuser