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



def resultados(request):
    """
    Página pública de resultados con datos ANONIMIZADOS.
    Muestra métricas agregadas, mapa interactivo y gráficos.
    """
    from auditorias.models import Empresa, Electricidad, GasNatural, CarbonMineral, FuelOil, Biomasa, GasPropano
    from django.db.models.functions import ExtractYear
    import json

    # =========================================================================
    # TODOS LOS PROYECTOS (para mostrar datos aunque no estén finalizados)
    # =========================================================================
    proyectos = ProyectoAuditoria.objects.all()
    centros = CentroPevi.objects.filter(activo=True)

    # =========================================================================
    # KPIs GLOBALES ANONIMIZADOS
    # =========================================================================
    total_proyectos = proyectos.count()
    total_centros = centros.count()

    # Empresas únicas atendidas (contamos sin revelar nombres)
    total_empresas = proyectos.values('empresa').distinct().count()

    # Sectores únicos
    sectores_unicos = Empresa.objects.filter(
        auditorias__isnull=False
    ).values_list('sector_productivo', flat=True).distinct().count()

    # Energía y Emisiones totales
    total_energia_kwh = 0.0
    total_emisiones_ton = 0.0

    # Energía por tipo de fuente
    energia_electricidad = 0.0
    energia_gas_natural = 0.0
    energia_carbon = 0.0
    energia_fuel_oil = 0.0
    energia_biomasa = 0.0
    energia_glp = 0.0

    for p in proyectos:
        total_energia_kwh += p.get_total_kwh()
        total_emisiones_ton += p.get_total_emisiones()

        # Sumar por tipo de energía
        elec = p.electricidad_related.first()
        if elec:
            energia_electricidad += elec.consumo_anual

        gas = p.gasnatural_related.first()
        if gas:
            energia_gas_natural += gas.consumo_anual_kwh

        carbon = p.carbonmineral_related.first()
        if carbon:
            energia_carbon += carbon.consumo_anual_kwh

        fuel = p.fueloil_related.first()
        if fuel:
            energia_fuel_oil += fuel.consumo_anual_kwh

        bio = p.biomasa_related.first()
        if bio:
            energia_biomasa += bio.consumo_anual_kwh

        glp = p.gaspropano_related.first()
        if glp:
            energia_glp += glp.consumo_anual_kwh

    # Convertir a MWh para visualización
    total_energia_mwh = total_energia_kwh / 1000 if total_energia_kwh > 0 else 0

    # =========================================================================
    # DATOS PARA MAPA (Centros con coordenadas)
    # =========================================================================
    centros_mapa = []
    for centro in centros:
        if centro.latitud and centro.longitud:
            proyectos_centro = proyectos.filter(centro=centro).count()
            centros_mapa.append({
                'nombre': centro.nombre_corto or centro.nombre,
                'lat': centro.latitud,
                'lng': centro.longitud,
                'proyectos': proyectos_centro,
                'color': centro.color_primario or '#1E40AF',
                'region': centro.region,
            })

    # =========================================================================
    # PROYECTOS POR AÑO (Evolución temporal)
    # =========================================================================
    proyectos_por_año = list(
        ProyectoAuditoria.objects.annotate(
            año=ExtractYear('fecha_inicio')
        ).values('año').annotate(
            total=Count('id')
        ).order_by('año')
    )[-6:]  # Últimos 6 años

    años_labels = [str(p['año']) for p in proyectos_por_año if p['año']]
    años_data = [p['total'] for p in proyectos_por_año if p['año']]

    # Si no hay datos, agregar valores por defecto
    if not años_labels:
        años_labels = ['2024', '2025']
        años_data = [0, 0]

    # =========================================================================
    # PROYECTOS POR SECTOR PRODUCTIVO (Anonimizado)
    # =========================================================================
    sectores_data = list(
        Empresa.objects.filter(
            auditorias__isnull=False
        ).values('sector_productivo').annotate(
            total=Count('auditorias', distinct=True)
        ).order_by('-total')[:8]
    )

    sectores_labels = [s['sector_productivo'] or 'Sin especificar' for s in sectores_data]
    sectores_valores = [s['total'] for s in sectores_data]

    # Si no hay datos, agregar valores por defecto
    if not sectores_labels:
        sectores_labels = ['Sin datos']
        sectores_valores = [0]

    # =========================================================================
    # PROYECTOS POR REGIÓN
    # =========================================================================
    regiones_data = list(
        proyectos.values('centro__region').annotate(
            total=Count('id')
        ).order_by('-total')
    )

    regiones_labels = [r['centro__region'] or 'Sin región' for r in regiones_data if r['centro__region']]
    regiones_valores = [r['total'] for r in regiones_data if r['centro__region']]

    # Si no hay datos, agregar valores por defecto para que el gráfico se muestre
    if not regiones_labels:
        regiones_labels = ['Sin datos']
        regiones_valores = [0]

    # =========================================================================
    # DISTRIBUCIÓN POR CENTRO (sin nombres de empresas)
    # =========================================================================
    centros_data = list(
        proyectos.values('centro__nombre_corto', 'centro__nombre').annotate(
            total=Count('id')
        ).order_by('-total')[:10]
    )

    centros_labels = [c['centro__nombre_corto'] or c['centro__nombre'] or 'Centro' for c in centros_data]
    centros_valores = [c['total'] for c in centros_data]

    # Si no hay datos, agregar valores por defecto
    if not centros_labels:
        centros_labels = ['Sin datos']
        centros_valores = [0]

    # =========================================================================
    # CONTEXTO FINAL
    # =========================================================================
    context = {
        # KPIs
        'total_proyectos': total_proyectos,
        'total_centros': total_centros,
        'total_empresas': total_empresas,
        'sectores_unicos': sectores_unicos,
        'total_energia_mwh': round(total_energia_mwh, 1),
        'total_emisiones_ton': round(total_emisiones_ton, 1),

        # Datos para mapa (JSON)
        'centros_mapa_json': json.dumps(centros_mapa),

        # Energía por tipo (JSON para gráfico)
        'energia_por_tipo_labels': json.dumps(['Electricidad', 'Gas Natural', 'Carbón', 'Fuel Oil', 'Biomasa', 'GLP']),
        'energia_por_tipo_data': json.dumps([
            round(energia_electricidad / 1000, 1),
            round(energia_gas_natural / 1000, 1),
            round(energia_carbon / 1000, 1),
            round(energia_fuel_oil / 1000, 1),
            round(energia_biomasa / 1000, 1),
            round(energia_glp / 1000, 1),
        ]),

        # Evolución temporal
        'años_labels': json.dumps(años_labels),
        'años_data': json.dumps(años_data),

        # Sectores
        'sectores_labels': json.dumps(sectores_labels),
        'sectores_data': json.dumps(sectores_valores),

        # Regiones
        'regiones_labels': json.dumps(regiones_labels),
        'regiones_data': json.dumps(regiones_valores),

        # Centros
        'centros_labels': json.dumps(centros_labels),
        'centros_data': json.dumps(centros_valores),
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