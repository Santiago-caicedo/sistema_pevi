from django.contrib import admin
from django.urls import path, include
from gestion.views import (
    cambiar_estado_proyecto, crear_empresa, crear_usuario, dashboard, crear_proyecto, detalle_proyecto, editar_proyecto, editar_usuario, eliminar_usuario, generar_informe_pdf,
    lista_proyectos, lista_empresas, lista_usuarios, registrar_consumo, registrar_produccion, subir_documento
)
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # ===========================================================================
    # SITIO WEB PÚBLICO (Raíz)
    # ===========================================================================
    path('', include('web.urls')),

    # ===========================================================================
    # ADMINISTRACIÓN DJANGO
    # ===========================================================================
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),

    # ===========================================================================
    # APLICACIÓN INTERNA (Panel de Gestión) - Prefijo /app/
    # ===========================================================================

    # --- DASHBOARD ---
    path('app/', dashboard, name='dashboard'),

    # --- EMPRESAS ---
    path('app/empresas/', lista_empresas, name='lista_empresas'),
    path('app/empresas/nueva/', crear_empresa, name='crear_empresa'),

    # --- PROYECTOS ---
    path('app/proyectos/', lista_proyectos, name='lista_proyectos'),
    path('app/proyectos/nuevo/', crear_proyecto, name='crear_proyecto'),

    # --- DETALLE Y GESTIÓN DE PROYECTO ---
    path('app/proyectos/<int:proyecto_id>/', detalle_proyecto, name='detalle_proyecto'),
    path('app/proyectos/<int:proyecto_id>/editar/', editar_proyecto, name='editar_proyecto'),
    path('app/proyectos/<int:proyecto_id>/documentos/subir/', subir_documento, name='subir_documento'),
    path('app/proyectos/<int:proyecto_id>/informe/pdf/', generar_informe_pdf, name='generar_informe_pdf'),
    path('app/proyectos/<int:proyecto_id>/estado/<str:nuevo_estado>/', cambiar_estado_proyecto, name='cambiar_estado'),

    # --- REGISTROS DE BITÁCORA ---
    path('app/proyectos/<int:proyecto_id>/registro/produccion/', registrar_produccion, name='registrar_produccion'),
    path('app/proyectos/<int:proyecto_id>/registro/<str:tipo_energia>/', registrar_consumo, name='registrar_consumo'),

    # --- GESTIÓN DE EQUIPO (RRHH) ---
    path('app/equipo/', lista_usuarios, name='lista_usuarios'),
    path('app/equipo/nuevo/', crear_usuario, name='crear_usuario'),
    path('app/equipo/<int:usuario_id>/editar/', editar_usuario, name='editar_usuario'),
    path('app/equipo/<int:usuario_id>/eliminar/', eliminar_usuario, name='eliminar_usuario'),

    # --- MÉTRICAS ---
    path('app/metricas/', include('metricas.urls')),
]

# Serving de archivos estáticos y media en desarrollo local
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)