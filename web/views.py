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
    # Agrupamos por Centro y contamos sus proyectos finalizados
    lista_centros = CentroPevi.objects.filter(activo=True).annotate(
        total_proyectos=Count('proyectoauditoria'),
        # Si tienes un campo de energía en el proyecto, podrías sumarlo así:
        # total_energia=Sum('proyectoauditoria__consumo_total_kwh') 
    ).order_by('-total_proyectos') # Los que más auditan salen primero
    
    regiones = CentroPevi.objects.filter(activo=True).values_list('region', flat=True).distinct()
    
    context = {
        'centros': lista_centros,
        'regiones': regiones
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