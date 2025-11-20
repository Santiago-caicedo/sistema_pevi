from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required

# Modelos
from auditorias.models import ProyectoAuditoria, Empresa

# Formularios Administrativos
from auditorias.forms import DocumentoForm, EmpresaForm, ProduccionForm, ProyectoForm

# Formularios de Energéticos (Bitácora Manual)
from auditorias.forms import (
    ElectricidadForm, GasNaturalForm, CarbonForm, 
    FuelOilForm, BiomasaForm, GasPropanoForm
)

# ==========================================
#  VISTAS DE GESTIÓN PRINCIPAL
# ==========================================

@login_required
def dashboard(request):
    """Panel principal con KPIs y listado."""
    proyectos = ProyectoAuditoria.objects.all().order_by('-created_at')[:5]
    
    context = {
        'total_proyectos': ProyectoAuditoria.objects.count(),
        'proyectos_activos': ProyectoAuditoria.objects.filter(estado='EJECUCION').count(),
        'lista_proyectos': proyectos
    }
    return render(request, 'gestion/dashboard.html', context)


@login_required
def registrar_produccion(request, proyecto_id):
    """Vista para registrar el contexto productivo (Bitácora)."""
    proyecto = get_object_or_404(ProyectoAuditoria, id=proyecto_id)
    
    if request.method == 'POST':
        # instance=proyecto es CLAVE para que ACTUALICE y no cree uno nuevo
        form = ProduccionForm(request.POST, instance=proyecto)
        if form.is_valid():
            form.save()
            messages.success(request, "Datos de producción actualizados correctamente.")
            return redirect('detalle_proyecto', proyecto_id=proyecto.id)
    else:
        form = ProduccionForm(instance=proyecto)

    context = {
        'proyecto': proyecto,
        'form': form,
        'titulo_energia': 'Contexto Productivo', # Reusamos el template
        'icono': 'bi-boxes'
    }
    # Reusamos el MISMO template bonito de registro de energía
    return render(request, 'gestion/registro_energia_form.html', context)


# ==========================================
#  LÓGICA DE PROYECTOS
# ==========================================

@login_required
def crear_proyecto(request):
    if request.method == 'POST':
        form = ProyectoForm(request.POST, user=request.user)
        if form.is_valid():
            proyecto = form.save(commit=False)
            if request.user.centro_pevi:
                proyecto.centro = request.user.centro_pevi
            proyecto.save()
            form.save_m2m()
            messages.success(request, "Proyecto creado exitosamente.")
            return redirect('detalle_proyecto', proyecto_id=proyecto.id)
    else:
        form = ProyectoForm(user=request.user)
    return render(request, 'gestion/proyecto_form.html', {'form': form})

@login_required
def detalle_proyecto(request, proyecto_id):
    """
    Hub del Proyecto: Muestra tarjetas, estado y calcula KPIs agregados.
    """
    proyecto = get_object_or_404(ProyectoAuditoria, id=proyecto_id)

    # 1. Recuperamos los registros de la Bitácora
    electricidad = proyecto.electricidad_related.first()
    gas_natural = proyecto.gasnatural_related.first()
    carbon = proyecto.carbonmineral_related.first()
    fuel_oil = proyecto.fueloil_related.first()
    biomasa = proyecto.biomasa_related.first()
    gas_propano = proyecto.gaspropano_related.first()

    # 2. Lista de fuentes activas
    fuentes_todas = [electricidad, gas_natural, carbon, fuel_oil, biomasa, gas_propano]
    fuentes_activas = [f for f in fuentes_todas if f is not None]

    # 3. Cálculo de Totales (KPIs)
    total_emisiones = 0.0
    total_costo = 0.0
    total_energia = 0.0

    for f in fuentes_activas:
        total_emisiones += f.emisiones_totales
        total_costo += f.costo_total_anual
        
        if hasattr(f, 'consumo_anual_kwh'): 
            total_energia += f.consumo_anual_kwh
        elif hasattr(f, 'consumo_anual'): 
            total_energia += f.consumo_anual

    # 4. Indicador IDES
    indicador_ides = 0
    if proyecto.produccion_total and proyecto.produccion_total > 0 and total_energia > 0:
        indicador_ides = total_energia / proyecto.produccion_total

    # 5. CORRECCIÓN DEL ERROR: Preparamos la producción como entero aquí
    produccion_display = 0
    if proyecto.produccion_total:
        produccion_display = round(proyecto.produccion_total)

    context = {
        'proyecto': proyecto,
        'produccion_display': produccion_display, # <--- Nueva variable limpia para el template
        
        # Objetos individuales
        'electricidad': electricidad,
        'gas_natural': gas_natural,
        'carbon_mineral': carbon,
        'fuel_oil': fuel_oil,
        'biomasa': biomasa,
        'gas_propano': gas_propano,
        
        # KPIs Redondeados
        'kpi_emisiones': round(total_emisiones, 2),
        'kpi_energia': round(total_energia),
        'kpi_costo': round(total_costo),
        'kpi_ides': round(indicador_ides, 4),
    }
    return render(request, 'gestion/proyecto_detalle.html', context)



@login_required
def lista_proyectos(request):
    """
    Listado de auditorías con filtro de seguridad por Centro PEVI.
    """
    # Optimización: select_related evita consultas repetidas a la BD para traer empresa y centro
    proyectos = ProyectoAuditoria.objects.select_related('empresa', 'centro').all().order_by('-created_at')

    # SEGURIDAD MULTI-TENANT:
    # Si el usuario pertenece a un centro, SOLO ve sus proyectos.
    if request.user.centro_pevi:
        proyectos = proyectos.filter(centro=request.user.centro_pevi)

    context = {
        'proyectos': proyectos,
        'usuario_centro': request.user.centro_pevi # Para mostrar en el título si aplica
    }
    return render(request, 'gestion/lista_proyectos.html', context)

@login_required
def crear_proyecto(request):
    """
    Creación de nuevo proyecto con asignación automática de Centro.
    """
    if request.method == 'POST':
        # Pasamos 'user' al form para que filtre las empresas (si es necesario)
        form = ProyectoForm(request.POST, user=request.user)
        
        if form.is_valid():
            proyecto = form.save(commit=False)
            
            # Asignación automática del Centro PEVI del usuario
            if request.user.centro_pevi:
                proyecto.centro = request.user.centro_pevi
            elif not proyecto.centro_id:
                # Si es superadmin y no eligió centro (caso borde), error o asignar default
                messages.error(request, "Como Admin Global, debes asignar un Centro PEVI.")
                return render(request, 'gestion/proyecto_form.html', {'form': form})

            proyecto.save()
            form.save_m2m() # Guarda la relación ManyToMany (Equipo de Ingenieros)
            
            messages.success(request, f"Proyecto '{proyecto.nombre_proyecto}' iniciado correctamente.")
            return redirect('detalle_proyecto', proyecto_id=proyecto.id)
    else:
        form = ProyectoForm(user=request.user)

    return render(request, 'gestion/proyecto_form.html', {'form': form})


# ==========================================
#  REGISTRO MANUAL DE ENERGÍA (BITÁCORA)
# ==========================================

# Mapa de configuración: Clave URL -> Formulario y Datos de Diseño
FORM_MAPPING = {
    'electricidad': {
        'form': ElectricidadForm, 
        'titulo': 'Energía Eléctrica', 
        'icono': 'bi-plug-fill'
    },
    'gas_natural': {
        'form': GasNaturalForm, 
        'titulo': 'Gas Natural', 
        'icono': 'bi-fire'
    },
    'carbon': {
        'form': CarbonForm, 
        'titulo': 'Carbón Mineral', 
        'icono': 'bi-box-seam-fill'
    },
    'fuel_oil': {
        'form': FuelOilForm, 
        'titulo': 'Fuel Oil / Diesel', 
        'icono': 'bi-droplet-fill'
    },
    'biomasa': {
        'form': BiomasaForm, 
        'titulo': 'Biomasa / Bagazo', 
        'icono': 'bi-recycle'
    },
    'gas_propano': {
        'form': GasPropanoForm, 
        'titulo': 'Gas Propano (GLP)', 
        'icono': 'bi-cloud-fog2-fill'
    },
}

@login_required
def registrar_consumo(request, proyecto_id, tipo_energia):
    """
    Vista Maestra: Maneja CUALQUIER tipo de formulario de energía.
    """
    proyecto = get_object_or_404(ProyectoAuditoria, id=proyecto_id)
    
    # 1. Validar que el tipo de energía existe en nuestro mapa
    config = FORM_MAPPING.get(tipo_energia)
    if not config:
        messages.error(request, "Tipo de energía no reconocido.")
        return redirect('detalle_proyecto', proyecto_id=proyecto.id)
    
    FormClass = config['form']

    # 2. Procesar Formulario
    if request.method == 'POST':
        form = FormClass(request.POST)
        if form.is_valid():
            registro = form.save(commit=False)
            registro.proyecto = proyecto # Asignamos el proyecto automáticamente
            registro.save()
            messages.success(request, f"Registro de {config['titulo']} guardado correctamente.")
            return redirect('detalle_proyecto', proyecto_id=proyecto.id)
        else:
            messages.error(request, "Error en el formulario. Verifique los datos.")
    else:
        form = FormClass()

    context = {
        'proyecto': proyecto,
        'form': form,
        'titulo_energia': config['titulo'],
        'icono': config['icono']
    }
    return render(request, 'gestion/registro_energia_form.html', context)



# ==========================================
#  GESTIÓN DE EMPRESAS
# ==========================================

@login_required
def lista_empresas(request):
    """Directorio completo de clientes."""
    empresas = Empresa.objects.all().order_by('razon_social')
    return render(request, 'gestion/lista_empresas.html', {'empresas': empresas})

@login_required
def crear_empresa(request):
    """Formulario para registrar un nuevo cliente."""
    if request.method == 'POST':
        form = EmpresaForm(request.POST)
        if form.is_valid():
            empresa = form.save()
            messages.success(request, f"Empresa '{empresa.razon_social}' registrada exitosamente.")
            return redirect('lista_empresas')
    else:
        form = EmpresaForm()
    
    return render(request, 'gestion/empresa_form.html', {'form': form})



@login_required
def subir_documento(request, proyecto_id):
    """Subir archivos adjuntos al proyecto."""
    proyecto = get_object_or_404(ProyectoAuditoria, id=proyecto_id)
    
    if request.method == 'POST':
        form = DocumentoForm(request.POST, request.FILES) # request.FILES es vital para archivos
        if form.is_valid():
            doc = form.save(commit=False)
            doc.proyecto = proyecto
            doc.save()
            messages.success(request, "Documento cargado exitosamente.")
            return redirect('detalle_proyecto', proyecto_id=proyecto.id)
    
    # Si es GET, redirigimos al detalle (usaremos un modal o una página aparte, 
    # pero por simplicidad redirigimos si intentan entrar por URL directa)
    return redirect('detalle_proyecto', proyecto_id=proyecto.id)