from django.shortcuts import render
from auditorias.models import ProyectoAuditoria
from gestion.models import CentroPevi
from .models import Noticia
from django.db.models import Sum

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
    """Directorio público de universidades."""
    # Traemos solo los activos y ordenados por región para agrupar visualmente si queremos
    lista_centros = CentroPevi.objects.filter(activo=True).order_by('region', 'nombre')
    
    # Obtenemos las regiones únicas para el filtro
    regiones = CentroPevi.objects.filter(activo=True).values_list('region', flat=True).distinct()
    
    context = {
        'centros': lista_centros,
        'regiones': regiones
    }
    return render(request, 'web/centros.html', context)