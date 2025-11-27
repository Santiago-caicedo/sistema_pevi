import json
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
from .forms import UsuarioEditarForm, UsuarioForm
from .models import Usuario

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
    Hub del Proyecto: 
    - Recupera bitácora energética.
    - Calcula totales y KPIs.
    - Prepara datos JSON para visualización con Chart.js.
    """
    proyecto = get_object_or_404(ProyectoAuditoria, id=proyecto_id)

    # 1. RECUPERAR OBJETOS DE BITÁCORA
    electricidad = proyecto.electricidad_related.first()
    gas_natural = proyecto.gasnatural_related.first()
    carbon = proyecto.carbonmineral_related.first()
    fuel_oil = proyecto.fueloil_related.first()
    biomasa = proyecto.biomasa_related.first()
    gas_propano = proyecto.gaspropano_related.first()

    # 2. CÁLCULO DE TOTALES (KPIs)
    # Lista de objetos para iterar
    fuentes_map = [
        ('Electricidad', electricidad),
        ('Gas Natural', gas_natural),
        ('Carbón Mineral', carbon),
        ('Fuel Oil', fuel_oil),
        ('Biomasa', biomasa),
        ('GLP', gas_propano),
    ]

    total_emisiones = 0.0
    total_costo = 0.0
    total_energia = 0.0

    # Listas para Chart.js
    chart_labels = []
    chart_data_energia = []
    chart_data_costos = []
    chart_colors = []

    # Mapa de colores corporativos (Bootstrap standard)
    color_map = {
        'Electricidad': '#ffc107',   # Amarillo
        'Gas Natural': '#0d6efd',    # Azul
        'Carbón Mineral': '#212529', # Negro
        'Fuel Oil': '#dc3545',       # Rojo
        'Biomasa': '#198754',        # Verde
        'GLP': '#0dcaf0'             # Cyan
    }

    for nombre, fuente in fuentes_map:
        if fuente:
            # A. Sumar Emisiones
            total_emisiones += fuente.emisiones_totales
            
            # B. Sumar Costos
            total_costo += fuente.costo_total_anual
            
            # C. Sumar Energía (Manejando polimorfismo de campos)
            energia_fuente = 0
            if hasattr(fuente, 'consumo_anual_kwh'): 
                energia_fuente = fuente.consumo_anual_kwh
            elif hasattr(fuente, 'consumo_anual'): 
                energia_fuente = fuente.consumo_anual
            
            total_energia += energia_fuente

            # D. Agregar datos a las Gráficas (Solo si hay consumo real)
            if energia_fuente > 0:
                chart_labels.append(nombre)
                chart_data_energia.append(round(energia_fuente))
                chart_data_costos.append(round(fuente.costo_total_anual))
                chart_colors.append(color_map.get(nombre, '#cccccc'))

    # 3. CÁLCULO INDICADOR DE DESEMPEÑO (IDES)
    indicador_ides = 0
    if proyecto.produccion_total and proyecto.produccion_total > 0 and total_energia > 0:
        indicador_ides = total_energia / proyecto.produccion_total

    # 4. PREPARACIÓN DE VISUALIZACIÓN DE PRODUCCIÓN
    produccion_display = 0
    if proyecto.produccion_total:
        produccion_display = round(proyecto.produccion_total)

    # 5. CONTEXTO FINAL
    context = {
        'proyecto': proyecto,
        
        # Objetos individuales (Para las tarjetas)
        'electricidad': electricidad,
        'gas_natural': gas_natural,
        'carbon_mineral': carbon,
        'fuel_oil': fuel_oil,
        'biomasa': biomasa,
        'gas_propano': gas_propano,
        'produccion_display': produccion_display,
        
        # KPIs Redondeados (Para evitar errores de template)
        'kpi_emisiones': round(total_emisiones, 2),
        'kpi_energia': round(total_energia),
        'kpi_costo': round(total_costo),
        'kpi_ides': round(indicador_ides, 4),
        
        # Datos JSON para Chart.js
        'chart_labels': json.dumps(chart_labels),
        'chart_data_energia': json.dumps(chart_data_energia),
        'chart_data_costos': json.dumps(chart_data_costos),
        'chart_colors': json.dumps(chart_colors),
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
    AHORA SOPORTA EDICIÓN: Si ya existe el dato, lo carga.
    """
    proyecto = get_object_or_404(ProyectoAuditoria, id=proyecto_id)
    
    # 1. Validar configuración
    config = FORM_MAPPING.get(tipo_energia)
    if not config:
        messages.error(request, "Tipo de energía no reconocido.")
        return redirect('detalle_proyecto', proyecto_id=proyecto.id)
    
    FormClass = config['form']
    
    # 2. BUSCAR SI YA EXISTE UN REGISTRO (Para editar en vez de crear)
    # Usamos el modelo vinculado al formulario para buscar en la BD
    ModelClass = FormClass._meta.model 
    registro_existente = ModelClass.objects.filter(proyecto=proyecto).first()

    # 3. Procesar Formulario
    if request.method == 'POST':
        # Pasamos 'instance' para que Django sepa que es una ACTUALIZACIÓN
        form = FormClass(request.POST, instance=registro_existente)
        
        if form.is_valid():
            registro = form.save(commit=False)
            registro.proyecto = proyecto # Aseguramos el vínculo
            registro.save()
            
            accion = "actualizado" if registro_existente else "creado"
            messages.success(request, f"Registro de {config['titulo']} {accion} correctamente.")
            return redirect('detalle_proyecto', proyecto_id=proyecto.id)
        else:
            messages.error(request, "Error en el formulario. Verifique los datos.")
    else:
        # Si es GET, cargamos el formulario con los datos existentes (si los hay)
        form = FormClass(instance=registro_existente)

    context = {
        'proyecto': proyecto,
        'form': form,
        'titulo_energia': config['titulo'],
        'icono': config['icono'],
        'es_edicion': registro_existente is not None # Para cambiar el texto del botón si quieres
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



# ==========================================
#  GESTIÓN DE EQUIPO (USUARIOS)
# ==========================================

@login_required
def lista_usuarios(request):
    """Directorio de personal filtrado por Centro PEVI."""
    usuarios = Usuario.objects.all().order_by('first_name')
    
    # FILTRO DE SEGURIDAD:
    # Si no es Superadmin, solo ve los de su centro
    if request.user.centro_pevi:
        usuarios = usuarios.filter(centro_pevi=request.user.centro_pevi)
        
    return render(request, 'gestion/lista_usuarios.html', {'usuarios': usuarios})

@login_required
def crear_usuario(request):
    """Registrar nuevo miembro del equipo."""
    if request.method == 'POST':
        form = UsuarioForm(request.POST)
        if form.is_valid():
            nuevo_usuario = form.save(commit=False)
            
            # ASIGNACIÓN AUTOMÁTICA DE CENTRO
            if request.user.centro_pevi:
                nuevo_usuario.centro_pevi = request.user.centro_pevi
            
            nuevo_usuario.save()
            messages.success(request, f"Usuario {nuevo_usuario.username} creado exitosamente.")
            return redirect('lista_usuarios')
    else:
        form = UsuarioForm()
    
    return render(request, 'gestion/usuario_form.html', {'form': form, 'titulo': 'Nuevo Usuario'})

@login_required
def editar_usuario(request, usuario_id):
    """Modificar datos de un miembro."""
    usuario = get_object_or_404(Usuario, id=usuario_id)
    
    # SEGURIDAD: Verificar que el usuario pertenezca al mismo centro (o ser superadmin)
    if request.user.centro_pevi and usuario.centro_pevi != request.user.centro_pevi:
        messages.error(request, "No tienes permiso para editar este usuario.")
        return redirect('lista_usuarios')

    if request.method == 'POST':
        form = UsuarioEditarForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, "Datos actualizados correctamente.")
            return redirect('lista_usuarios')
    else:
        form = UsuarioEditarForm(instance=usuario)
        
    return render(request, 'gestion/usuario_form.html', {'form': form, 'titulo': 'Editar Usuario'})

@login_required
def eliminar_usuario(request, usuario_id):
    """Eliminar (o desactivar) usuario."""
    usuario = get_object_or_404(Usuario, id=usuario_id)
    
    # SEGURIDAD
    if request.user.centro_pevi and usuario.centro_pevi != request.user.centro_pevi:
        messages.error(request, "Acción no permitida.")
        return redirect('lista_usuarios')
        
    # Evitar auto-suicidio
    if usuario == request.user:
        messages.error(request, "No puedes eliminarte a ti mismo.")
        return redirect('lista_usuarios')

    usuario.delete()
    messages.success(request, "Usuario eliminado del sistema.")
    return redirect('lista_usuarios')