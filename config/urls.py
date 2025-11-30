from django.contrib import admin
from django.urls import path, include
from gestion.views import (
    crear_empresa, dashboard, crear_proyecto, detalle_proyecto, generar_informe_pdf, 
    lista_proyectos, lista_empresas, registrar_consumo, registrar_produccion, subir_documento
)
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    
    path('', dashboard, name='dashboard'),
    path('empresas/', lista_empresas, name='lista_empresas'),
    path('empresas/nueva/', crear_empresa, name='crear_empresa'),
    
    path('proyectos/', lista_proyectos, name='lista_proyectos'),
    path('proyectos/nuevo/', crear_proyecto, name='crear_proyecto'),
    
    # 1. Rutas específicas del proyecto
    path('proyectos/<int:proyecto_id>/', detalle_proyecto, name='detalle_proyecto'),
    path('proyectos/<int:proyecto_id>/documentos/subir/', subir_documento, name='subir_documento'),

    # =========================================================================
    # 2. RUTA ESPECÍFICA (ESTA DEBE IR PRIMERO) - ¡IMPORTANTE!
    # =========================================================================
    path('proyectos/<int:proyecto_id>/registro/produccion/', registrar_produccion, name='registrar_produccion'),

    # =========================================================================
    # 3. RUTA GENÉRICA / DINÁMICA (ESTA DEBE IR AL FINAL)
    # Django usará esta solo si no coincidió con "produccion" ni "documentos"
    # =========================================================================
    path('proyectos/<int:proyecto_id>/registro/<str:tipo_energia>/', registrar_consumo, name='registrar_consumo'),

    path('proyectos/<int:proyecto_id>/informe/pdf/', generar_informe_pdf, name='generar_informe_pdf'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)