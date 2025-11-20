from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, CentroPevi

# 1. Registrar Centro PEVI
@admin.register(CentroPevi)
class CentroPeviAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'codigo_interno', 'region', 'activo')
    search_fields = ('nombre', 'codigo_interno')
    list_filter = ('region', 'activo')

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