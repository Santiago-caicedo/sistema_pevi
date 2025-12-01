import json
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.core.exceptions import PermissionDenied

# Modelos
from auditorias.models import ProyectoAuditoria
from gestion.models import CentroPevi, Usuario
from gestion.decorators import solo_directivos

@login_required
@solo_directivos
def dashboard_estrategico(request):
    """
    Dashboard de Inteligencia de Negocio (BI).
    Calcula métricas globales, desglose técnico y permite filtrado dinámico.
    """
    user = request.user
    
    # ---------------------------------------------------------
    # 1. DEFINICIÓN DEL ALCANCE (SCOPE DE SEGURIDAD)
    # ---------------------------------------------------------
    if user.is_superuser or user.rol == 'DIRECTOR_NACIONAL':
        # Ve todos los proyectos a nivel nacional
        qs = ProyectoAuditoria.objects.select_related('empresa', 'lider_proyecto', 'centro').all()
        titulo_scope = "Consolidado Nacional"
    elif user.rol == 'DIRECTOR_CENTRO':
        # Ve solo los proyectos de su centro
        qs = ProyectoAuditoria.objects.filter(centro=user.centro_pevi).select_related('empresa', 'lider_proyecto')
        titulo_scope = f"Centro: {user.centro_pevi.nombre}"
    else:
        raise PermissionDenied("Acceso restringido a directivos.")

    # ---------------------------------------------------------
    # 2. APLICACIÓN DE FILTROS ACTIVOS (QUERYSET PRINCIPAL)
    # ---------------------------------------------------------
    filtro_proyecto = request.GET.get('proyecto')
    filtro_lider = request.GET.get('lider')
    # filtro_anio = request.GET.get('anio') # Disponible para futuro

    if filtro_proyecto:
        qs = qs.filter(id=filtro_proyecto)
    
    if filtro_lider:
        qs = qs.filter(lider_proyecto_id=filtro_lider)

    # ---------------------------------------------------------
    # 3. MOTOR DE AGREGACIÓN (CÁLCULOS MATEMÁTICOS)
    # ---------------------------------------------------------
    
    # Acumuladores Globales
    global_kwh_electrico = 0.0
    global_kwh_termico = 0.0
    global_costo_total = 0.0
    global_emisiones_total = 0.0

    # Diccionario para acumular por Fuente (Para Gráficas)
    sources_agg = {
        'Electricidad':   {'kwh': 0, 'costo': 0, 'color': '#ffc107'}, # Amarillo
        'Gas Natural':    {'kwh': 0, 'costo': 0, 'color': '#0d6efd'}, # Azul
        'Carbón Mineral': {'kwh': 0, 'costo': 0, 'color': '#212529'}, # Negro
        'Fuel Oil':       {'kwh': 0, 'costo': 0, 'color': '#dc3545'}, # Rojo
        'Biomasa':        {'kwh': 0, 'costo': 0, 'color': '#198754'}, # Verde
        'GLP':            {'kwh': 0, 'costo': 0, 'color': '#0dcaf0'}, # Cyan
    }

    # Lista para la Tabla Detallada
    tabla_proyectos = []

    # Optimización de Base de Datos (Traer todo en una sola consulta grande)
    proyectos_data = qs.prefetch_related(
        'electricidad_related', 'gasnatural_related', 'carbonmineral_related',
        'fueloil_related', 'biomasa_related', 'gaspropano_related'
    )

    for p in proyectos_data:
        # Variables locales del proyecto
        p_kwh_elec = 0
        p_kwh_term = 0
        p_costo = 0
        p_emis = 0
        
        # Mapeo de todas las fuentes posibles
        mapa_fuentes = [
            ('Electricidad', p.electricidad_related.first()),
            ('Gas Natural', p.gasnatural_related.first()),
            ('Carbón Mineral', p.carbonmineral_related.first()),
            ('Fuel Oil', p.fueloil_related.first()),
            ('Biomasa', p.biomasa_related.first()),
            ('GLP', p.gaspropano_related.first()),
        ]

        for nombre, obj in mapa_fuentes:
            if obj:
                # A. Normalizar Energía a kWh
                energia = 0
                if hasattr(obj, 'consumo_anual_kwh'): energia = obj.consumo_anual_kwh
                elif hasattr(obj, 'consumo_anual'): energia = obj.consumo_anual
                
                # B. Clasificar (Eléctrico vs Térmico)
                if nombre == 'Electricidad': 
                    p_kwh_elec += energia
                else: 
                    p_kwh_term += energia
                
                # C. Sumar Costos y Emisiones
                p_costo += obj.costo_total_anual
                p_emis += obj.emisiones_totales

                # D. Sumar al Agregado por Fuente
                sources_agg[nombre]['kwh'] += energia
                sources_agg[nombre]['costo'] += obj.costo_total_anual

        # Sumar a los Acumuladores Globales del Dashboard
        global_kwh_electrico += p_kwh_elec
        global_kwh_termico += p_kwh_term
        global_costo_total += p_costo
        global_emisiones_total += p_emis
        
        # Calcular IDES del proyecto individual
        p_energia_total = p_kwh_elec + p_kwh_term
        p_ides = 0
        if p.produccion_total > 0:
            # Redondeo aquí para enviar dato limpio al template
            p_ides = round(p_energia_total / p.produccion_total, 2)

        # Agregar fila a la tabla de detalle
        tabla_proyectos.append({
            'objeto': p, # Objeto completo (para ID y Nombre)
            'empresa': p.empresa.razon_social,
            'lider': p.lider_proyecto.get_full_name() if p.lider_proyecto else "Sin asignar",
            'produccion': round(p.produccion_total),
            'unidad_prod': p.unidad_produccion,
            'energia_total': round(p_energia_total),
            'energia_elec': round(p_kwh_elec),
            'energia_term': round(p_kwh_term),
            'costo': round(p_costo),
            'emisiones': round(p_emis, 2),
            'ides': p_ides
        })

    # ---------------------------------------------------------
    # 4. PREPARACIÓN DE DATOS VISUALES (GRÁFICAS)
    # ---------------------------------------------------------
    
    # A. Datos para Chart.js (Dona y Barras de Costos)
    chart_labels = []
    data_kwh = []
    data_costo = []
    colors = []

    for key, val in sources_agg.items():
        if val['kwh'] > 0: # Solo incluimos fuentes que tengan consumo
            chart_labels.append(key)
            data_kwh.append(round(val['kwh']))
            data_costo.append(round(val['costo']))
            colors.append(val['color'])

    # B. Datos para Balance MBTU (Eléctrico vs Térmico)
    FACTOR_MBTU = 0.00341214
    mbtu_elec = global_kwh_electrico * FACTOR_MBTU
    mbtu_term = global_kwh_termico * FACTOR_MBTU
    
    # Array simple [Elec, Term]
    data_mbtu = [round(mbtu_elec, 2), round(mbtu_term, 2)]

    # ---------------------------------------------------------
    # 5. LISTAS PARA FILTROS (LÓGICA EN CASCADA)
    # ---------------------------------------------------------
    
    # A. Definir Scope Base según Rol
    if user.rol == 'DIRECTOR_CENTRO':
        # Base: Solo su centro
        lista_proyectos_dropdown = ProyectoAuditoria.objects.filter(centro=user.centro_pevi)
        lista_lideres_dropdown = Usuario.objects.filter(centro_pevi=user.centro_pevi, rol__in=['PROFESOR', 'DIRECTOR_CENTRO'])
    else:
        # Base: Todo el país
        lista_proyectos_dropdown = ProyectoAuditoria.objects.all()
        lista_lideres_dropdown = Usuario.objects.filter(rol__in=['PROFESOR', 'DIRECTOR_CENTRO', 'DIRECTOR_NACIONAL'])

    # B. FILTRO EN CASCADA (Dependent Dropdown Logic)
    # Si hay un líder seleccionado, la lista de proyectos se reduce SOLO a los de ese líder
    if filtro_lider:
        lista_proyectos_dropdown = lista_proyectos_dropdown.filter(lider_proyecto_id=filtro_lider)

    # ---------------------------------------------------------
    # 6. CONTEXTO FINAL (RETURN)
    # ---------------------------------------------------------
    context = {
        'page_title': "Dashboard de Ingeniería",
        'page_subtitle': titulo_scope,
        
        # Filtros y Listas
        'opciones_proyectos': lista_proyectos_dropdown, # Lista inteligente filtrada
        'opciones_lideres': lista_lideres_dropdown,
        'filtro_actual_proyecto': int(filtro_proyecto) if filtro_proyecto else '',
        'filtro_actual_lider': int(filtro_lider) if filtro_lider else '',

        # KPIs Globales (Tarjetas Superiores)
        'kpi_proyectos': len(tabla_proyectos),
        'kpi_energia_total': round(global_kwh_electrico + global_kwh_termico),
        'kpi_costo_total': round(global_costo_total),
        'kpi_emisiones': round(global_emisiones_total, 2),
        
        # Desglose Técnico (Tarjeta Balance)
        'kpi_elec_kwh': round(global_kwh_electrico),
        'kpi_term_mbtu': round(mbtu_term, 2),

        # Tabla Detallada
        'tabla_proyectos': tabla_proyectos,

        # JSON Charts (Serializados para JavaScript)
        'chart_labels': json.dumps(chart_labels),
        'chart_data_energia': json.dumps(data_kwh),
        'chart_data_costos': json.dumps(data_costo),
        'chart_colors': json.dumps(colors),
        'chart_data_mbtu': json.dumps(data_mbtu),
    }

    return render(request, 'metricas/dashboard_estrategico.html', context)



@login_required
@solo_directivos
def dashboard_nacional(request):
    """
    Tablero de Mando Nacional con capacidad Drill-Down.
    Modo 1: Visión País (Ranking de Centros).
    Modo 2: Visión Centro (Detalle de Ingeniería específico).
    """
    user = request.user
    
    # 1. SEGURIDAD ESTRICTA
    if not (user.is_superuser or user.rol == 'DIRECTOR_NACIONAL'):
        raise PermissionDenied("Acceso exclusivo a Dirección Nacional.")

    # 2. SELECTOR DE CENTROS
    centros = CentroPevi.objects.filter(activo=True).order_by('nombre')
    filtro_centro_id = request.GET.get('centro')
    
    # Contexto base
    context = {
        'page_title': "Tablero Nacional",
        'opciones_centros': centros,
        'filtro_actual_centro': int(filtro_centro_id) if filtro_centro_id else '',
    }

    # =========================================================
    # MODO A: VISTA DETALLADA DE UN CENTRO (DRILL-DOWN)
    # =========================================================
    if filtro_centro_id:
        centro_seleccionado = centros.get(id=filtro_centro_id)
        context['page_subtitle'] = f"Análisis Detallado: {centro_seleccionado.nombre}"
        context['vista_detalle'] = True # Bandera para el template

        # Obtenemos proyectos SOLO de este centro
        qs = ProyectoAuditoria.objects.filter(centro=centro_seleccionado).select_related('empresa', 'lider_proyecto')
        
        # --- (Aquí reutilizamos la lógica de agregación del BI) ---
        global_kwh_electrico = 0.0
        global_kwh_termico = 0.0
        global_costo_total = 0.0
        global_emisiones_total = 0.0

        sources_agg = {
            'Electricidad':   {'kwh': 0, 'costo': 0, 'color': '#ffc107'},
            'Gas Natural':    {'kwh': 0, 'costo': 0, 'color': '#0d6efd'},
            'Carbón Mineral': {'kwh': 0, 'costo': 0, 'color': '#212529'},
            'Fuel Oil':       {'kwh': 0, 'costo': 0, 'color': '#dc3545'},
            'Biomasa':        {'kwh': 0, 'costo': 0, 'color': '#198754'},
            'GLP':            {'kwh': 0, 'costo': 0, 'color': '#0dcaf0'},
        }

        tabla_proyectos = []
        proyectos_data = qs.prefetch_related(
            'electricidad_related', 'gasnatural_related', 'carbonmineral_related',
            'fueloil_related', 'biomasa_related', 'gaspropano_related'
        )

        for p in proyectos_data:
            p_kwh_elec = 0
            p_kwh_term = 0
            p_costo = 0
            p_emis = 0
            
            mapa = [
                ('Electricidad', p.electricidad_related.first()),
                ('Gas Natural', p.gasnatural_related.first()),
                ('Carbón Mineral', p.carbonmineral_related.first()),
                ('Fuel Oil', p.fueloil_related.first()),
                ('Biomasa', p.biomasa_related.first()),
                ('GLP', p.gaspropano_related.first()),
            ]

            for nombre, obj in mapa:
                if obj:
                    eng = 0
                    if hasattr(obj, 'consumo_anual_kwh'): eng = obj.consumo_anual_kwh
                    elif hasattr(obj, 'consumo_anual'): eng = obj.consumo_anual
                    
                    if nombre == 'Electricidad': p_kwh_elec += eng
                    else: p_kwh_term += eng
                    
                    p_costo += obj.costo_total_anual
                    p_emis += obj.emisiones_totales
                    sources_agg[nombre]['kwh'] += eng
                    sources_agg[nombre]['costo'] += obj.costo_total_anual

            global_kwh_electrico += p_kwh_elec
            global_kwh_termico += p_kwh_term
            global_costo_total += p_costo
            global_emisiones_total += p_emis
            
            p_ides = 0
            if p.produccion_total > 0:
                p_ides = round((p_kwh_elec + p_kwh_term) / p.produccion_total, 2)

            tabla_proyectos.append({
                'objeto': p,
                'empresa': p.empresa.razon_social,
                'lider': p.lider_proyecto.get_full_name() if p.lider_proyecto else "-",
                'produccion': round(p.produccion_total),
                'unidad_prod': p.unidad_produccion,
                'energia_total': round(p_kwh_elec + p_kwh_term),
                'costo': round(p_costo),
                'emisiones': round(p_emis, 2),
                'ides': p_ides
            })

        # Preparar Gráficas de Detalle
        chart_labels = []
        data_kwh = []
        data_costo = []
        colors = []
        for key, val in sources_agg.items():
            if val['kwh'] > 0:
                chart_labels.append(key)
                data_kwh.append(round(val['kwh']))
                data_costo.append(round(val['costo']))
                colors.append(val['color'])

        FACTOR_MBTU = 0.00341214
        data_mbtu = [round(global_kwh_electrico * FACTOR_MBTU, 2), round(global_kwh_termico * FACTOR_MBTU, 2)]

        # Actualizar Contexto con Datos de Detalle
        context.update({
            'kpi_proyectos': len(tabla_proyectos),
            'kpi_energia': round(global_kwh_electrico + global_kwh_termico),
            'kpi_costo': round(global_costo_total),
            'kpi_emisiones': round(global_emisiones_total, 2),
            'kpi_elec_kwh': round(global_kwh_electrico),
            'kpi_term_mbtu': round(global_kwh_termico * FACTOR_MBTU, 2),
            'tabla_proyectos': tabla_proyectos,
            'chart_labels': json.dumps(chart_labels),
            'chart_data_energia': json.dumps(data_kwh),
            'chart_data_costos': json.dumps(data_costo),
            'chart_colors': json.dumps(colors),
            'chart_data_mbtu': json.dumps(data_mbtu),
        })

    # =========================================================
    # MODO B: VISTA COMPARATIVA NACIONAL (DEFAULT)
    # =========================================================
    else:
        context['page_subtitle'] = "Visión consolidada de la red PEVI"
        context['vista_detalle'] = False # Bandera
        
        data_centros = []
        nac_proyectos = 0
        nac_energia = 0
        nac_emisiones = 0

        for c in centros:
            proyectos = ProyectoAuditoria.objects.filter(centro=c)
            c_qty = proyectos.count()
            c_energia = sum(p.get_total_kwh() for p in proyectos)
            c_emisiones = sum(p.get_total_emisiones() for p in proyectos)
            
            nac_proyectos += c_qty
            nac_energia += c_energia
            nac_emisiones += c_emisiones
            
            data_centros.append({
                'nombre': c.nombre,
                'region': c.region,
                'proyectos': c_qty,
                'energia': round(c_energia),
                'emisiones': round(c_emisiones, 2),
                'promedio_kwh': round(c_energia / c_qty) if c_qty > 0 else 0
            })

        # Datos Comparativos
        data_centros.sort(key=lambda x: x['energia'], reverse=True)
        chart_labels = [d['nombre'] for d in data_centros]
        chart_data_energia = [d['energia'] for d in data_centros]
        chart_data_proyectos = [d['proyectos'] for d in data_centros]

        context.update({
            'kpi_centros': centros.count(),
            'kpi_proyectos': nac_proyectos,
            'kpi_energia': round(nac_energia),
            'kpi_emisiones': round(nac_emisiones, 2),
            'tabla_centros': data_centros,
            'chart_labels': json.dumps(chart_labels),
            'chart_data_energia': json.dumps(chart_data_energia),
            'chart_data_proyectos': json.dumps(chart_data_proyectos),
        })
    
    return render(request, 'metricas/dashboard_nacional.html', context)