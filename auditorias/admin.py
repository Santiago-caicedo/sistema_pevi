from django.contrib import admin
from .models import (
    Empresa, ProyectoAuditoria, DocumentoProyecto,
    Electricidad, GasNatural, CarbonMineral, FuelOil, Biomasa, GasPropano
)

@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('razon_social', 'nit', 'sector_productivo', 'ciudad')
    search_fields = ('razon_social', 'nit')

@admin.register(ProyectoAuditoria)
class ProyectoAdmin(admin.ModelAdmin):
    list_display = ('nombre_proyecto', 'empresa', 'centro', 'estado', 'fecha_inicio')
    list_filter = ('estado', 'centro')
    filter_horizontal = ('equipo',)

admin.site.register(DocumentoProyecto)

# --- ADMINS PARA LOS ENERGÉTICOS (Actualizado a la Bitácora Manual) ---

@admin.register(Electricidad)
class ElectricidadAdmin(admin.ModelAdmin):
    # Electricidad usa 'consumo_anual'
    list_display = ('proyecto', 'consumo_anual', 'costo_total_anual', 'emisiones_totales')
    list_filter = ('proyecto__centro',)

class CombustibleAdmin(admin.ModelAdmin):
    # Los combustibles usan 'consumo_anual_orig' (Unidad Original)
    list_display = ('proyecto', 'consumo_anual_orig', 'costo_total_anual', 'emisiones_totales')
    list_filter = ('proyecto__centro',)

# Registramos los combustibles usando la clase CombustibleAdmin
admin.site.register(GasNatural, CombustibleAdmin)
admin.site.register(CarbonMineral, CombustibleAdmin)
admin.site.register(FuelOil, CombustibleAdmin)
admin.site.register(Biomasa, CombustibleAdmin)
admin.site.register(GasPropano, CombustibleAdmin)