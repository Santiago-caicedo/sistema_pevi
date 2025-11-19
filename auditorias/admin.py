from django.contrib import admin
from .models import Empresa, ProyectoAuditoria, DocumentoProyecto
from .models import Electricidad, GasNatural, CarbonMineral, FuelOil, Biomasa, GasPropano

@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('razon_social', 'nit', 'sector_productivo', 'ciudad')
    search_fields = ('razon_social', 'nit')

@admin.register(ProyectoAuditoria)
class ProyectoAdmin(admin.ModelAdmin):
    list_display = ('nombre_proyecto', 'empresa', 'centro', 'estado', 'fecha_inicio')
    list_filter = ('estado', 'centro')
    filter_horizontal = ('equipo',) # Widget bonito para seleccionar usuarios multiples

admin.site.register(DocumentoProyecto)


# Un admin personalizado para ver los cálculos automáticos
class EnergeticoAdmin(admin.ModelAdmin):
    list_display = ('proyecto', 'consumo_total_anual', 'costo_total_anual', 'calcular_emisiones_show')
    
    def calcular_emisiones_show(self, obj):
        return f"{obj.calcular_emisiones_ton_co2():.2f} TonCO2"
    calcular_emisiones_show.short_description = "Emisiones Calculadas"

admin.site.register(Electricidad, EnergeticoAdmin)
admin.site.register(GasNatural, EnergeticoAdmin)
admin.site.register(CarbonMineral, EnergeticoAdmin)
admin.site.register(FuelOil, EnergeticoAdmin)
admin.site.register(Biomasa, EnergeticoAdmin)
admin.site.register(GasPropano, EnergeticoAdmin)