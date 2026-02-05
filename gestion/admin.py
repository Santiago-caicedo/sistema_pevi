from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, CentroPevi

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