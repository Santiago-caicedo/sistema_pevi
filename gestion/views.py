import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.db.models import Sum

# Librería PDF
from weasyprint import HTML
import tempfile

# Modelos y Formularios del Sistema
from .models import Usuario
from .forms import UsuarioForm, UsuarioEditarForm
from auditorias.models import ProyectoAuditoria, Empresa
from auditorias.forms import (
    ProyectoForm, ProduccionForm, DocumentoForm, EmpresaForm,
    ElectricidadForm, GasNaturalForm, CarbonForm, 
    FuelOilForm, BiomasaForm, GasPropanoForm
)

# Decoradores de Seguridad Personalizados
from .decorators import acceso_staff, solo_directivos, solo_lideres

# ==============================================================================
#  CONFIGURACIÓN GLOBAL
# ==============================================================================

# Mapa de configuración para la Bitácora de Energía
# Define qué formulario, título y lógica física usa cada tipo
FORM_MAPPING = {
    'electricidad': {
        'form': ElectricidadForm, 
        'titulo': 'Energía Eléctrica', 
        'icono': 'bi-plug-fill',
        'tipo_fisica': 'electricidad' 
    },
    'gas_natural': {
        'form': GasNaturalForm, 
        'titulo': 'Gas Natural', 
        'icono': 'bi-fire',
        'tipo_fisica': 'volumen' # Requiere PC en kJ/m3
    },
    'carbon': {
        'form': CarbonForm, 
        'titulo': 'Carbón Mineral', 
        'icono': 'bi-box-seam-fill',
        'tipo_fisica': 'masa' # Requiere PC en kJ/kg
    },
    'fuel_oil': {
        'form': FuelOilForm, 
        'titulo': 'Fuel Oil / Diesel', 
        'icono': 'bi-droplet-fill',
        'tipo_fisica': 'volumen'
    },
    'biomasa': {
        'form': BiomasaForm, 
        'titulo': 'Biomasa / Bagazo', 
        'icono': 'bi-recycle',
        'tipo_fisica': 'masa'
    },
    'gas_propano': {
        'form': GasPropanoForm, 
        'titulo': 'Gas Propano (GLP)', 
        'icono': 'bi-cloud-fog2-fill',
        'tipo_fisica': 'masa'
    },
}

def verificar_acceso_proyecto(user, proyecto):
    """
    Helper de Seguridad: Valida si un usuario tiene derecho a ver/editar un proyecto específico.
    """
    if user.is_superuser or user.rol == 'DIRECTOR_NACIONAL':
        return True
    if user.rol == 'DIRECTOR_CENTRO' and proyecto.centro == user.centro_pevi:
        return True
    if user.rol == 'PROFESOR' and proyecto.lider_proyecto == user:
        return True
    if user.rol == 'ESTUDIANTE' and proyecto.equipo.filter(id=user.id).exists():
        return True
    return False

# ==============================================================================
#  1. DASHBOARD Y LISTADOS (Vistas de Resumen)
# ==============================================================================

@login_required
@acceso_staff
def dashboard(request):
    user = request.user
    
    # Política Default Deny: Empezamos vacío
    proyectos = ProyectoAuditoria.objects.none()
    titulo = "Bienvenido"

    # Lógica de Gobernanza de Datos (Filtros por Rol)
    if user.is_superuser or user.rol == 'DIRECTOR_NACIONAL':
        proyectos = ProyectoAuditoria.objects.all()
        titulo = "Vista Nacional Consolidada"
    elif user.rol == 'DIRECTOR_CENTRO':
        if user.centro_pevi:
            proyectos = ProyectoAuditoria.objects.filter(centro=user.centro_pevi)
            titulo = f"Gestión {user.centro_pevi.nombre}"
    elif user.rol == 'PROFESOR':
        proyectos = ProyectoAuditoria.objects.filter(lider_proyecto=user)
        titulo = "Mis Proyectos (Líder)"
    elif user.rol == 'ESTUDIANTE':
        proyectos = ProyectoAuditoria.objects.filter(equipo=user)
        titulo = "Mis Asignaciones"

    # Cálculo rápido de KPI Global (Suma de consumos de los proyectos visibles)
    # Nota: Asegúrate de haber agregado el método get_total_kwh() al modelo ProyectoAuditoria
    total_kwh_global = sum([p.get_total_kwh() for p in proyectos])

    context = {
        'lista_proyectos': proyectos.order_by('-created_at')[:5],
        'total_proyectos': proyectos.count(),
        'proyectos_activos': proyectos.filter(estado='EJECUCION').count(),
        'kpi_total_energia': round(total_kwh_global),
        'page_subtitle': titulo
    }
    return render(request, 'gestion/dashboard.html', context)

@login_required
@acceso_staff
def lista_proyectos(request):
    user = request.user
    proyectos = ProyectoAuditoria.objects.none()

    # Mismos filtros de seguridad que el Dashboard
    if user.is_superuser or user.rol == 'DIRECTOR_NACIONAL':
        proyectos = ProyectoAuditoria.objects.select_related('empresa', 'centro').all()
    elif user.rol == 'DIRECTOR_CENTRO':
        proyectos = ProyectoAuditoria.objects.filter(centro=user.centro_pevi)
    elif user.rol == 'PROFESOR':
        proyectos = ProyectoAuditoria.objects.filter(lider_proyecto=user)
    elif user.rol == 'ESTUDIANTE':
        proyectos = ProyectoAuditoria.objects.filter(equipo=user)

    return render(request, 'gestion/lista_proyectos.html', {
        'proyectos': proyectos.order_by('-created_at'),
        'usuario_centro': user.centro_pevi
    })

# ==============================================================================
#  2. GESTIÓN ADMINISTRATIVA (Empresas y Equipo)
#  Seguridad: Solo Directores y Superadmin
# ==============================================================================

@login_required
@solo_directivos
def lista_empresas(request):
    empresas = Empresa.objects.all().order_by('razon_social')
    return render(request, 'gestion/lista_empresas.html', {'empresas': empresas})

@login_required
@solo_directivos
def crear_empresa(request):
    if request.method == 'POST':
        form = EmpresaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Empresa registrada exitosamente.")
            return redirect('lista_empresas')
    else:
        form = EmpresaForm()
    return render(request, 'gestion/empresa_form.html', {'form': form})

@login_required
@solo_directivos
def lista_usuarios(request):
    user = request.user
    usuarios = Usuario.objects.none()

    if user.is_superuser or user.rol == 'DIRECTOR_NACIONAL':
        usuarios = Usuario.objects.all().order_by('first_name')
    else:
        # Director de Centro solo ve su propia gente
        if user.centro_pevi:
            usuarios = Usuario.objects.filter(centro_pevi=user.centro_pevi).order_by('first_name')
    
    return render(request, 'gestion/lista_usuarios.html', {'usuarios': usuarios})

@login_required
@solo_directivos
def crear_usuario(request):
    if request.method == 'POST':
        # Pasamos creator=request.user para activar la seguridad
        form = UsuarioForm(request.POST, creator=request.user)
        if form.is_valid():
            nuevo = form.save(commit=False)
            
            # Forzamos asignación de centro (Seguridad extra)
            if request.user.centro_pevi and not request.user.is_superuser:
                nuevo.centro_pevi = request.user.centro_pevi
                
            # Forzamos que NO sea superusuario ni staff (Seguridad extra)
            nuevo.is_superuser = False
            nuevo.is_staff = False
            
            nuevo.save()
            messages.success(request, f"Usuario {nuevo.username} creado.")
            return redirect('lista_usuarios')
    else:
        form = UsuarioForm(creator=request.user)
        
    return render(request, 'gestion/usuario_form.html', {'form': form, 'titulo': 'Nuevo Usuario'})

@login_required
@solo_directivos
def editar_usuario(request, usuario_id):
    target_user = get_object_or_404(Usuario, id=usuario_id)
    
    # Seguridad cruzada
    if not request.user.is_superuser and request.user.rol != 'DIRECTOR_NACIONAL':
        if target_user.centro_pevi != request.user.centro_pevi:
            raise PermissionDenied("No puedes editar personal de otro centro.")

    if request.method == 'POST':
        # Pasamos creator=request.user
        form = UsuarioEditarForm(request.POST, instance=target_user, creator=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Usuario actualizado.")
            return redirect('lista_usuarios')
    else:
        form = UsuarioEditarForm(instance=target_user, creator=request.user)
        
    return render(request, 'gestion/usuario_form.html', {'form': form, 'titulo': 'Editar Usuario'})

@login_required
@solo_directivos
def eliminar_usuario(request, usuario_id):
    target_user = get_object_or_404(Usuario, id=usuario_id)
    
    if not request.user.is_superuser and request.user.rol != 'DIRECTOR_NACIONAL':
        if target_user.centro_pevi != request.user.centro_pevi:
            raise PermissionDenied("No tienes permiso para eliminar este usuario.")
    
    if target_user == request.user:
        messages.error(request, "No puedes eliminarte a ti mismo.")
    else:
        target_user.delete()
        messages.success(request, "Usuario eliminado del sistema.")
    return redirect('lista_usuarios')

# ==============================================================================
#  3. GESTIÓN DE PROYECTOS (CRUD)
#  Seguridad: Solo Líderes (Directores y Profesores)
# ==============================================================================

@login_required
@solo_lideres
def crear_proyecto(request):
    if request.method == 'POST':
        form = ProyectoForm(request.POST, user=request.user)
        if form.is_valid():
            proyecto = form.save(commit=False)
            # Asignar centro del creador
            if request.user.centro_pevi:
                proyecto.centro = request.user.centro_pevi
            elif not proyecto.centro_id and not request.user.is_superuser:
                 raise PermissionDenied("Error de asignación de Centro. Contacte soporte.")
            
            proyecto.save()
            form.save_m2m() # Guardar equipo
            messages.success(request, "Proyecto iniciado correctamente.")
            return redirect('detalle_proyecto', proyecto_id=proyecto.id)
    else:
        form = ProyectoForm(user=request.user)
    return render(request, 'gestion/proyecto_form.html', {'form': form, 'titulo': 'Nuevo Proyecto'})

@login_required
@solo_lideres
def editar_proyecto(request, proyecto_id):
    proyecto = get_object_or_404(ProyectoAuditoria, id=proyecto_id)
    
    # Validar propiedad
    es_propietario = (proyecto.lider_proyecto == request.user)
    es_director_suyo = (request.user.rol == 'DIRECTOR_CENTRO' and proyecto.centro == request.user.centro_pevi)
    
    if not (es_propietario or es_director_suyo or request.user.is_superuser):
        raise PermissionDenied("Solo el líder o director pueden editar la estructura del proyecto.")

    if request.method == 'POST':
        form = ProyectoForm(request.POST, instance=proyecto, user=request.user)
        if form.is_valid():
            form.save()
            form.save_m2m()
            messages.success(request, "Proyecto actualizado.")
            return redirect('detalle_proyecto', proyecto_id=proyecto.id)
    else:
        form = ProyectoForm(instance=proyecto, user=request.user)
    return render(request, 'gestion/proyecto_form.html', {'form': form, 'titulo': 'Editar Proyecto'})

# ==============================================================================
#  4. HUB DEL PROYECTO (Lógica Core)
#  Seguridad: Acceso Staff (Incluye Estudiantes asignados)
# ==============================================================================

@login_required
@acceso_staff
def detalle_proyecto(request, proyecto_id):
    proyecto = get_object_or_404(ProyectoAuditoria, id=proyecto_id)
    
    # 🚨 BLINDAJE DE SEGURIDAD
    if not verificar_acceso_proyecto(request.user, proyecto):
        raise PermissionDenied("Acceso Denegado: No estás autorizado para ver este proyecto.")

    # 1. Recuperar Bitácora Energética
    electricidad = proyecto.electricidad_related.first()
    gas_natural = proyecto.gasnatural_related.first()
    carbon = proyecto.carbonmineral_related.first()
    fuel_oil = proyecto.fueloil_related.first()
    biomasa = proyecto.biomasa_related.first()
    gas_propano = proyecto.gaspropano_related.first()

    # 2. Cálculos de Totales (KPIs)
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
    
    total_kwh_electrico = 0.0
    total_kwh_termico = 0.0

    # Listas para Chart.js
    chart_labels = []
    chart_data_energia = []
    chart_data_costos = []
    chart_colors = []

    color_map = {
        'Electricidad': '#ffc107', 'Gas Natural': '#0d6efd',
        'Carbón Mineral': '#212529', 'Fuel Oil': '#dc3545',
        'Biomasa': '#198754', 'GLP': '#0dcaf0'
    }

    for nombre, fuente in fuentes_map:
        if fuente:
            total_emisiones += fuente.emisiones_totales
            total_costo += fuente.costo_total_anual
            
            # Polimorfismo: Obtener kWh
            energia_fuente = 0
            if hasattr(fuente, 'consumo_anual_kwh'): 
                energia_fuente = fuente.consumo_anual_kwh
            elif hasattr(fuente, 'consumo_anual'): 
                energia_fuente = fuente.consumo_anual
            
            total_energia += energia_fuente

            if nombre == 'Electricidad':
                total_kwh_electrico += energia_fuente
            else:
                total_kwh_termico += energia_fuente

            if energia_fuente > 0:
                chart_labels.append(nombre)
                chart_data_energia.append(round(energia_fuente))
                chart_data_costos.append(round(fuente.costo_total_anual))
                chart_colors.append(color_map.get(nombre, '#cccccc'))

    # 3. MBTU (Millones de BTU)
    FACTOR_MBTU = 0.00341214
    mbtu_electrico = total_kwh_electrico * FACTOR_MBTU
    mbtu_termico = total_kwh_termico * FACTOR_MBTU
    chart_data_mbtu = [round(mbtu_electrico, 2), round(mbtu_termico, 2)]

    # 4. IDES (Indicador de Desempeño)
    indicador_ides = 0
    if proyecto.produccion_total and proyecto.produccion_total > 0 and total_energia > 0:
        indicador_ides = total_energia / proyecto.produccion_total

    # 5. Producción Display (Entero)
    produccion_display = 0
    if proyecto.produccion_total:
        produccion_display = round(proyecto.produccion_total)

    context = {
        'proyecto': proyecto,
        'produccion_display': produccion_display,
        
        # Objetos Individuales
        'electricidad': electricidad,
        'gas_natural': gas_natural,
        'carbon_mineral': carbon,
        'fuel_oil': fuel_oil,
        'biomasa': biomasa,
        'gas_propano': gas_propano,
        
        # KPIs Numéricos
        'kpi_emisiones': round(total_emisiones, 2),
        'kpi_energia': round(total_energia),
        'kpi_costo': round(total_costo),
        'kpi_ides': round(indicador_ides, 4),
        'kpi_elec_kwh': round(total_kwh_electrico),
        'kpi_term_mbtu': round(mbtu_termico, 2),

        # Datos Gráficos JSON
        'chart_labels': json.dumps(chart_labels),
        'chart_data_energia': json.dumps(chart_data_energia),
        'chart_data_costos': json.dumps(chart_data_costos),
        'chart_colors': json.dumps(chart_colors),
        'chart_data_mbtu': json.dumps(chart_data_mbtu),
        
        # Permisos frontend
        'puede_editar_estructura': (request.user.rol != 'ESTUDIANTE'),
    }
    
    return render(request, 'gestion/proyecto_detalle.html', context)

# ==============================================================================
#  5. VISTAS OPERATIVAS (Registros, Archivos, PDF)
# ==============================================================================

@login_required
@acceso_staff
def registrar_consumo(request, proyecto_id, tipo_energia):
    proyecto = get_object_or_404(ProyectoAuditoria, id=proyecto_id)
    
    # Seguridad
    if not verificar_acceso_proyecto(request.user, proyecto):
        raise PermissionDenied("No tienes permiso para modificar este proyecto.")

    config = FORM_MAPPING.get(tipo_energia)
    if not config:
        messages.error(request, "Tipo de energía no válido.")
        return redirect('detalle_proyecto', proyecto_id=proyecto.id)
    
    FormClass = config['form']
    ModelClass = FormClass._meta.model 
    registro_existente = ModelClass.objects.filter(proyecto=proyecto).first()

    if request.method == 'POST':
        form = FormClass(request.POST, instance=registro_existente)
        if form.is_valid():
            registro = form.save(commit=False)
            registro.proyecto = proyecto
            registro.save()
            
            accion = "actualizado" if registro_existente else "creado"
            messages.success(request, f"Registro de {config['titulo']} {accion}.")
            return redirect('detalle_proyecto', proyecto_id=proyecto.id)
    else:
        form = FormClass(instance=registro_existente)

    context = {
        'proyecto': proyecto,
        'form': form,
        'titulo_energia': config['titulo'],
        'icono': config['icono'],
        'tipo_fisica': config.get('tipo_fisica', 'masa'),
        'es_edicion': registro_existente is not None
    }
    return render(request, 'gestion/registro_energia_form.html', context)

@login_required
@acceso_staff
def registrar_produccion(request, proyecto_id):
    proyecto = get_object_or_404(ProyectoAuditoria, id=proyecto_id)
    
    if not verificar_acceso_proyecto(request.user, proyecto):
        raise PermissionDenied("Acceso denegado.")
    
    if request.method == 'POST':
        form = ProduccionForm(request.POST, instance=proyecto)
        if form.is_valid():
            form.save()
            messages.success(request, "Contexto productivo actualizado.")
            return redirect('detalle_proyecto', proyecto_id=proyecto.id)
    else:
        form = ProduccionForm(instance=proyecto)

    # Renderiza el formulario específico de producción
    return render(request, 'gestion/produccion_form.html', {'proyecto': proyecto, 'form': form})

@login_required
@acceso_staff
def subir_documento(request, proyecto_id):
    proyecto = get_object_or_404(ProyectoAuditoria, id=proyecto_id)
    
    if not verificar_acceso_proyecto(request.user, proyecto):
        raise PermissionDenied("Acceso denegado.")
    
    if request.method == 'POST':
        form = DocumentoForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.proyecto = proyecto
            doc.save()
            messages.success(request, "Documento cargado.")
    return redirect('detalle_proyecto', proyecto_id=proyecto.id)

@login_required
@acceso_staff
def generar_informe_pdf(request, proyecto_id):
    proyecto = get_object_or_404(ProyectoAuditoria, id=proyecto_id)
    
    if not verificar_acceso_proyecto(request.user, proyecto):
        raise PermissionDenied("Acceso denegado.")

    # Recuperación de datos (Similar a detalle_proyecto pero formateado para PDF)
    electricidad = proyecto.electricidad_related.first()
    gas_natural = proyecto.gasnatural_related.first()
    carbon = proyecto.carbonmineral_related.first()
    fuel_oil = proyecto.fueloil_related.first()
    biomasa = proyecto.biomasa_related.first()
    gas_propano = proyecto.gaspropano_related.first()

    fuentes_map = [
        ('Electricidad', electricidad, 'kWh'),
        ('Gas Natural', gas_natural, 'm³'),
        ('Carbón Mineral', carbon, 'Ton'),
        ('Fuel Oil', fuel_oil, 'Gal'),
        ('Biomasa', biomasa, 'Ton'),
        ('GLP', gas_propano, 'kg'),
    ]

    total_emisiones = 0.0
    total_costo = 0.0
    total_energia = 0.0
    total_kwh_electrico = 0.0
    total_kwh_termico = 0.0

    datos_tabla = []

    for nombre_bonito, fuente, unidad in fuentes_map:
        if fuente:
            total_emisiones += fuente.emisiones_totales
            total_costo += fuente.costo_total_anual
            
            energia_kwh = 0
            consumo_orig = 0
            if hasattr(fuente, 'consumo_anual_kwh'): 
                energia_kwh = fuente.consumo_anual_kwh
                consumo_orig = fuente.consumo_anual_orig
            elif hasattr(fuente, 'consumo_anual'): 
                energia_kwh = fuente.consumo_anual
                consumo_orig = fuente.consumo_anual
            
            total_energia += energia_kwh

            if nombre_bonito == 'Electricidad':
                total_kwh_electrico += energia_kwh
            else:
                total_kwh_termico += energia_kwh

            # Pre-formateo para evitar errores en template
            datos_tabla.append({
                'nombre': nombre_bonito,
                'unidad': unidad,
                'consumo': f"{consumo_orig:,.0f}",
                'energia': f"{energia_kwh:,.0f}",
                'emisiones': f"{fuente.emisiones_totales:,.2f}",
                'costo': f"{fuente.costo_total_anual:,.0f}"
            })

    indicador_ides = 0
    if proyecto.produccion_total and proyecto.produccion_total > 0 and total_energia > 0:
        indicador_ides = total_energia / proyecto.produccion_total

    context = {
        'proyecto': proyecto,
        'datos_tabla': datos_tabla,
        'kpi_emisiones': f"{total_emisiones:,.2f}",
        'kpi_energia': f"{total_energia:,.0f}",
        'kpi_costo': f"{total_costo:,.0f}",
        'kpi_ides': f"{indicador_ides:,.2f}",
        'kpi_elec': f"{total_kwh_electrico:,.0f}",
        'kpi_term': f"{total_kwh_termico:,.0f}",
        'base_url': request.build_absolute_uri('/') 
    }

    html_string = render_to_string('gestion/informe_pdf.html', context)
    html = HTML(string=html_string, base_url=request.build_absolute_uri())
    result = html.write_pdf()

    response = HttpResponse(result, content_type='application/pdf')
    filename = f"Informe_PEVI_{proyecto.id}.pdf"
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    return response