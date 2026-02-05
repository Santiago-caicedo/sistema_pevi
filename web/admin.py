from django.contrib import admin
from .models import Noticia


@admin.register(Noticia)
class NoticiaAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'autor', 'fecha_publicacion', 'publicada']
    list_filter = ['publicada', 'fecha_publicacion']
    search_fields = ['titulo', 'resumen', 'contenido']
    prepopulated_fields = {'slug': ('titulo',)}
    list_editable = ['publicada']
    date_hierarchy = 'fecha_publicacion'
    ordering = ['-fecha_publicacion']

    fieldsets = (
        ('Contenido', {
            'fields': ('titulo', 'slug', 'imagen_portada', 'resumen', 'contenido')
        }),
        ('Publicación', {
            'fields': ('autor', 'publicada'),
            'classes': ('collapse',)
        }),
    )
