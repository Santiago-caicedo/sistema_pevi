from django.contrib import admin
from django.urls import path, include
from gestion.views import (
    cambiar_estado_proyecto, crear_empresa, editar_empresa, crear_usuario, dashboard, crear_proyecto, detalle_proyecto, editar_proyecto, editar_usuario, eliminar_usuario, generar_informe_pdf,
    lista_proyectos, lista_empresas, lista_usuarios, registrar_consumo, registrar_produccion, subir_documento, guardar_reduccion,
    crear_oportunidad, editar_oportunidad, eliminar_oportunidad,
    # Panel de Control Superadmin
    control_panel, control_centros_lista, control_centro_crear, control_centro_editar, control_centro_eliminar,
    control_usuarios_lista, control_usuario_crear, control_usuario_editar, control_usuario_eliminar,
    control_noticias_lista, control_noticia_crear, control_noticia_editar, control_noticia_eliminar
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
    path('app/empresas/<int:empresa_id>/editar/', editar_empresa, name='editar_empresa'),

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

    # --- OPORTUNIDADES DE MEJORA ---
    path('app/proyectos/<int:proyecto_id>/reduccion/', guardar_reduccion, name='guardar_reduccion'),
    path('app/proyectos/<int:proyecto_id>/oportunidades/nueva/', crear_oportunidad, name='crear_oportunidad'),
    path('app/proyectos/<int:proyecto_id>/oportunidades/<int:opm_id>/editar/', editar_oportunidad, name='editar_oportunidad'),
    path('app/proyectos/<int:proyecto_id>/oportunidades/<int:opm_id>/eliminar/', eliminar_oportunidad, name='eliminar_oportunidad'),

    # --- GESTIÓN DE EQUIPO (RRHH) ---
    path('app/equipo/', lista_usuarios, name='lista_usuarios'),
    path('app/equipo/nuevo/', crear_usuario, name='crear_usuario'),
    path('app/equipo/<int:usuario_id>/editar/', editar_usuario, name='editar_usuario'),
    path('app/equipo/<int:usuario_id>/eliminar/', eliminar_usuario, name='eliminar_usuario'),

    # --- MÉTRICAS ---
    path('app/metricas/', include('metricas.urls')),

    # ===========================================================================
    # PANEL DE CONTROL SUPERADMIN - Prefijo /app/control/
    # ===========================================================================
    path('app/control/', control_panel, name='control_panel'),

    # --- Centros PEVI ---
    path('app/control/centros/', control_centros_lista, name='control_centros_lista'),
    path('app/control/centros/nuevo/', control_centro_crear, name='control_centro_crear'),
    path('app/control/centros/<int:centro_id>/editar/', control_centro_editar, name='control_centro_editar'),
    path('app/control/centros/<int:centro_id>/eliminar/', control_centro_eliminar, name='control_centro_eliminar'),

    # --- Usuarios ---
    path('app/control/usuarios/', control_usuarios_lista, name='control_usuarios_lista'),
    path('app/control/usuarios/nuevo/', control_usuario_crear, name='control_usuario_crear'),
    path('app/control/usuarios/<int:usuario_id>/editar/', control_usuario_editar, name='control_usuario_editar'),
    path('app/control/usuarios/<int:usuario_id>/eliminar/', control_usuario_eliminar, name='control_usuario_eliminar'),

    # --- Noticias ---
    path('app/control/noticias/', control_noticias_lista, name='control_noticias_lista'),
    path('app/control/noticias/nueva/', control_noticia_crear, name='control_noticia_crear'),
    path('app/control/noticias/<int:noticia_id>/editar/', control_noticia_editar, name='control_noticia_editar'),
    path('app/control/noticias/<int:noticia_id>/eliminar/', control_noticia_eliminar, name='control_noticia_eliminar'),
]

# Serving de archivos estáticos y media en desarrollo local
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)