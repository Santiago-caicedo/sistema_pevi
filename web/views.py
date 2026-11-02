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
            'total_energia_mwh': int(total_energia / 1000),  # Convertir a MWh
            'total_emisiones': int(total_emisiones),
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



def resultados(request):
    """
    Boletín público de resultados del Programa PEVI (datos ANONIMIZADOS).
    Cifras agregadas, matriz energética, cobertura territorial y series,
    todas filtrables por año, región y sector.
    """
    from auditorias.models import Empresa
    from django.db.models.functions import ExtractYear
    from django.utils import timezone

    # =========================================================================
    # FILTROS DESDE GET PARAMS
    # =========================================================================
    filtro_año = request.GET.get('año', '')
    filtro_region = request.GET.get('region', '')
    filtro_sector = request.GET.get('sector', '')

    # Opciones de los filtros (sin filtrar)
    años_disponibles = [
        a for a in ProyectoAuditoria.objects.annotate(año=ExtractYear('fecha_inicio'))
        .values_list('año', flat=True).distinct().order_by('-año') if a
    ]
    regiones_disponibles = [
        r for r in CentroPevi.objects.filter(activo=True)
        .values_list('region', flat=True).distinct().order_by('region') if r
    ]
    sectores_disponibles = [
        s for s in Empresa.objects.filter(auditorias__isnull=False)
        .values_list('sector_productivo', flat=True).distinct().order_by('sector_productivo') if s
    ]

    # =========================================================================
    # PROYECTOS BASE (con filtros)
    # =========================================================================
    proyectos = ProyectoAuditoria.objects.all()
    centros = CentroPevi.objects.filter(activo=True)

    if filtro_año.isdigit():
        proyectos = proyectos.filter(fecha_inicio__year=int(filtro_año))
    if filtro_region:
        proyectos = proyectos.filter(centro__region=filtro_region)
    if filtro_sector:
        proyectos = proyectos.filter(empresa__sector_productivo=filtro_sector)

    # =========================================================================
    # CIFRAS PRINCIPALES
    # =========================================================================
    total_proyectos = proyectos.count()
    total_centros = centros.count()
    total_empresas = proyectos.values('empresa').distinct().count()
    sectores_unicos = (
        proyectos.exclude(empresa__sector_productivo='')
        .values('empresa__sector_productivo').distinct().count()
    )

    # Energía (kWh) y emisiones, total y por fuente
    FUENTES = [
        # (clave, nombre, relación, campo kWh, color institucional)
        ('electricidad', 'Electricidad', 'electricidad_related', 'consumo_anual', '#004884'),
        ('gas_natural', 'Gas natural', 'gasnatural_related', 'consumo_anual_kwh', '#3E7CB1'),
        ('carbon', 'Carbón mineral', 'carbonmineral_related', 'consumo_anual_kwh', '#4A4F57'),
        ('fuel_oil', 'Fuel oil', 'fueloil_related', 'consumo_anual_kwh', '#8C5A2B'),
        ('biomasa', 'Biomasa', 'biomasa_related', 'consumo_anual_kwh', '#4E7F3A'),
        ('glp', 'GLP (gas propano)', 'gaspropano_related', 'consumo_anual_kwh', '#B7791F'),
    ]
    energia_kwh = {clave: 0.0 for clave, *_ in FUENTES}
    total_energia_kwh = 0.0
    total_emisiones_ton = 0.0

    for p in proyectos.prefetch_related(*[rel for _, _, rel, _, _ in FUENTES]):
        total_energia_kwh += p.get_total_kwh()
        total_emisiones_ton += p.get_total_emisiones()
        for clave, _, rel, campo, _ in FUENTES:
            registro = next(iter(getattr(p, rel).all()), None)
            if registro:
                energia_kwh[clave] += getattr(registro, campo) or 0

    total_energia_mwh = total_energia_kwh / 1000
    suma_fuentes = sum(energia_kwh.values())
    matriz_energia = [
        {
            'nombre': nombre,
            'mwh': round(energia_kwh[clave] / 1000),
            'pct': (energia_kwh[clave] / suma_fuentes * 100) if suma_fuentes else 0,
            'color': color,
        }
        for clave, nombre, _, _, color in FUENTES
    ]
    matriz_energia.sort(key=lambda f: f['mwh'], reverse=True)

    # =========================================================================
    # COBERTURA TERRITORIAL (centros con proyectos filtrados)
    # =========================================================================
    conteo_por_centro = dict(
        proyectos.values_list('centro').annotate(total=Count('id')).values_list('centro', 'total')
    )
    centros_tabla = sorted(
        [
            {
                'nombre': c.nombre,
                'sigla': c.nombre_corto or c.nombre,
                'ciudad': c.ciudad,
                'region': c.region,
                'proyectos': conteo_por_centro.get(c.id, 0),
                # Solo coordenadas válidas (un dato mal digitado no debe romper el mapa)
                'lat': c.latitud if c.latitud is not None and -90 <= c.latitud <= 90 else None,
                'lng': c.longitud if c.longitud is not None and -180 <= c.longitud <= 180 else None,
            }
            for c in centros
        ],
        key=lambda c: (-c['proyectos'], c['nombre']),
    )

    # =========================================================================
    # SERIES (todas respetan los filtros)
    # =========================================================================
    serie_anual = [
        {'etiqueta': str(r['año']), 'valor': r['total']}
        for r in proyectos.annotate(año=ExtractYear('fecha_inicio'))
        .values('año').annotate(total=Count('id')).order_by('año')
        if r['año']
    ]
    serie_sectores = [
        {'etiqueta': r['empresa__sector_productivo'] or 'Sin especificar', 'valor': r['total']}
        for r in proyectos.values('empresa__sector_productivo')
        .annotate(total=Count('id')).order_by('-total')[:8]
    ]
    serie_regiones = [
        {'etiqueta': r['centro__region'], 'valor': r['total']}
        for r in proyectos.exclude(centro__region='').exclude(centro__region__isnull=True)
        .values('centro__region').annotate(total=Count('id')).order_by('-total')
    ]
    serie_centros = [
        {'etiqueta': c['sigla'], 'valor': c['proyectos']}
        for c in centros_tabla if c['proyectos']
    ]

    # Texto "Mostrando: ..." del resumen de filtros
    resumen_filtros = ' · '.join([
        filtro_año or 'Todos los años',
        filtro_region or 'Todas las regiones',
        filtro_sector or 'Todos los sectores',
    ])

    context = {
        'fecha_corte': timezone.localdate(),
        'total_proyectos': total_proyectos,
        'total_centros': total_centros,
        'total_empresas': total_empresas,
        'sectores_unicos': sectores_unicos,
        'total_energia_mwh': round(total_energia_mwh),
        'total_emisiones_ton': round(total_emisiones_ton),
        'matriz_energia': matriz_energia,
        'centros_tabla': centros_tabla,
        'serie_anual': serie_anual,
        'serie_sectores': serie_sectores,
        'serie_regiones': serie_regiones,
        'serie_centros': serie_centros,

        # Filtros
        'años_disponibles': años_disponibles,
        'regiones_disponibles': regiones_disponibles,
        'sectores_disponibles': sectores_disponibles,
        'filtro_año': filtro_año,
        'filtro_region': filtro_region,
        'filtro_sector': filtro_sector,
        'hay_filtros': bool(filtro_año or filtro_region or filtro_sector),
        'resumen_filtros': resumen_filtros,

        # Datos para gráficos, mapa y exportación (vía json_script, sin |safe)
        'datos_graficos': {
            'mapa': [c for c in centros_tabla if c['lat'] is not None and c['lng'] is not None],
            'anual': serie_anual,
            'sectores': serie_sectores,
            'regiones': serie_regiones,
            'centros': serie_centros,
            'matriz': matriz_energia,
            'resumen_filtros': resumen_filtros,
            'indicadores': [
                ['Auditorías registradas', total_proyectos],
                ['Empresas atendidas', total_empresas],
                ['Centros PEVI activos', total_centros],
                ['Sectores productivos', sectores_unicos],
                ['Energía analizada (MWh/año)', round(total_energia_mwh)],
                ['Emisiones reportadas (t CO2/año)', round(total_emisiones_ton)],
            ],
        },
    }

    return render(request, 'web/resultados.html', context)


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