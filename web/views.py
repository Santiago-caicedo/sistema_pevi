from django.shortcuts import render
from auditorias.models import ProyectoAuditoria
from gestion.models import CentroPevi
from .models import Noticia
from django.db.models import Count, Sum

def home(request):
    """Página de inicio (Landing Page)."""
    
    # 1. KPIs PÚBLICOS (Transparencia)
    total_proyectos = ProyectoAuditoria.objects.filter(estado='FINALIZADO').count()
    total_centros = CentroPevi.objects.filter(activo=True).count()
    
    # Suma aproximada de energía (anonimizada)
    # Nota: Usamos una lógica simplificada o caché en producción para no recalcular todo siempre
    # Por ahora, usamos un count rápido.
    
    # 2. NOTICIAS RECIENTES
    noticias = Noticia.objects.filter(publicada=True).order_by('-fecha_publicacion')[:3]

    context = {
        'kpi_proyectos': total_proyectos,
        'kpi_centros': total_centros,
        'noticias': noticias
    }
    return render(request, 'web/home.html', context)

def nosotros(request):
    return render(request, 'web/nosotros.html')

def centros(request):
    """
    Directorio público de universidades con métricas calculadas.
    """
    from auditorias.models import Empresa
    import json

    # Obtenemos los centros activos
    lista_centros = CentroPevi.objects.filter(activo=True).order_by('nombre')

    # Regiones únicas para el filtro
    regiones = CentroPevi.objects.filter(activo=True).values_list('region', flat=True).distinct()

    # Total de proyectos para el hero
    total_proyectos = ProyectoAuditoria.objects.count()

    # Calcular métricas detalladas por cada centro
    centros_con_metricas = []
    for centro in lista_centros:
        proyectos = ProyectoAuditoria.objects.filter(centro=centro)
        proyectos_finalizados = proyectos.filter(estado='FINALIZADO')

        # Métricas de energía y emisiones
        total_energia = 0.0
        total_emisiones = 0.0
        for p in proyectos_finalizados:
            total_energia += p.get_total_kwh()
            total_emisiones += p.get_total_emisiones()

        # Distribución por estado para gráfico
        estados_count = {
            'borrador': proyectos.filter(estado='BORRADOR').count(),
            'ejecucion': proyectos.filter(estado='EJECUCION').count(),
            'finalizado': proyectos_finalizados.count(),
        }

        # Sectores industriales únicos
        sectores = Empresa.objects.filter(
            auditorias__centro=centro
        ).values_list('sector_productivo', flat=True).distinct()[:5]

        # Proyectos por año (últimos 5 años)
        from django.db.models.functions import ExtractYear
        proyectos_por_año_qs = proyectos.annotate(
            año=ExtractYear('fecha_inicio')
        ).values('año').annotate(
            total=Count('id')
        ).order_by('año')

        # Convertir a lista y tomar los últimos 5
        proyectos_por_año = list(proyectos_por_año_qs)[-5:]

        años_labels = [str(p['año']) for p in proyectos_por_año if p['año']]
        años_data = [p['total'] for p in proyectos_por_año if p['año']]

        centros_con_metricas.append({
            'centro': centro,
            'total_energia_mwh': round(total_energia / 1000, 1),  # Convertir a MWh
            'total_emisiones': round(total_emisiones, 1),
            'estados_json': json.dumps(list(estados_count.values())),
            'sectores': list(sectores),
            'años_labels': json.dumps(años_labels),
            'años_data': json.dumps(años_data),
            'proyectos_finalizados': proyectos_finalizados.count(),
        })

    context = {
        'centros': centros_con_metricas,
        'regiones': regiones,
        'total_proyectos': total_proyectos,
        'total_centros': lista_centros.count(),
    }
    return render(request, 'web/centros.html', context)



def biblioteca(request):
    """Repositorio de documentación técnica."""
    
    # Simulación de Base de Datos de Documentos
    documentos = [
        {
            'titulo': 'Optimización de Sistemas de Bombeo',
            'categoria': 'Uso Final de Energía',
            'autor': 'UPME',
            'descripcion': 'Guía técnica para el diagnóstico y mejora de la eficiencia en sistemas de bombeo industrial, incluyendo curvas características y selección de equipos.',
            'imagen': 'cover_bombeo.png',
            'link': 'https://www1.upme.gov.co/DemandaEnergetica/EEIColombia/Manual_sistemas_bombeo.pdf'
        },
        {
            'titulo': 'Sistemas de Fuerza Motriz',
            'categoria': 'Electrificación',
            'autor': 'UPME',
            'descripcion': 'Manual de buenas prácticas para la gestión de motores eléctricos industriales, variadores de frecuencia y calidad de potencia.',
            'imagen': 'cover_motores.png',
            'link': 'https://www1.upme.gov.co/DemandaEnergetica/EEIColombia/Manual_sistemas_fuerza_motriz.pdf'
        },
        {
            'titulo': 'Optimización de Sistemas de Vapor',
            'categoria': 'Energía Térmica',
            'autor': 'UPME',
            'descripcion': 'Estrategias para la generación, distribución y recuperación de condensados en calderas y redes de vapor industrial.',
            'imagen': 'cover_vapor.png',
            'link': 'https://www1.upme.gov.co/DemandaEnergetica/EEIColombia/Manual_sistemas_vapor.pdf'
        },
    ]

    return render(request, 'web/biblioteca.html', {'documentos': documentos})