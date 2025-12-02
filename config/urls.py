from django.contrib import admin
from django.urls import path, include
from gestion.views import (
    cambiar_estado_proyecto, crear_empresa, crear_usuario, dashboard, crear_proyecto, detalle_proyecto, editar_proyecto, editar_usuario, eliminar_usuario, generar_informe_pdf, 
    lista_proyectos, lista_empresas, lista_usuarios, registrar_consumo, registrar_produccion, subir_documento
)
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    
    # --- DASHBOARD ---
    path('', dashboard, name='dashboard'),
    
    # --- EMPRESAS ---
    path('empresas/', lista_empresas, name='lista_empresas'),
    path('empresas/nueva/', crear_empresa, name='crear_empresa'),
    
    # --- PROYECTOS ---
    path('proyectos/', lista_proyectos, name='lista_proyectos'),
    path('proyectos/nuevo/', crear_proyecto, name='crear_proyecto'),
    
    # --- DETALLE Y GESTIÓN DE PROYECTO ---
    path('proyectos/<int:proyecto_id>/', detalle_proyecto, name='detalle_proyecto'),
    path('proyectos/<int:proyecto_id>/editar/', editar_proyecto, name='editar_proyecto'),
    path('proyectos/<int:proyecto_id>/documentos/subir/', subir_documento, name='subir_documento'),
    path('proyectos/<int:proyecto_id>/informe/pdf/', generar_informe_pdf, name='generar_informe_pdf'),
    path('proyectos/<int:proyecto_id>/estado/<str:nuevo_estado>/', cambiar_estado_proyecto, name='cambiar_estado'),

    # --- REGISTROS DE BITÁCORA (Orden Importante) ---
    path('proyectos/<int:proyecto_id>/registro/produccion/', registrar_produccion, name='registrar_produccion'),
    path('proyectos/<int:proyecto_id>/registro/<str:tipo_energia>/', registrar_consumo, name='registrar_consumo'),

    # --- GESTIÓN DE EQUIPO (RRHH) - NUEVAS RUTAS ---
    path('equipo/', lista_usuarios, name='lista_usuarios'),
    path('equipo/nuevo/', crear_usuario, name='crear_usuario'),
    path('equipo/<int:usuario_id>/editar/', editar_usuario, name='editar_usuario'),
    path('equipo/<int:usuario_id>/eliminar/', eliminar_usuario, name='eliminar_usuario'),


    # RUTA MÉTRICAS
    path('metricas/', include('metricas.urls')),


    path('web/', include('web.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)