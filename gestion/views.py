import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.db.models import Sum, Q
from django.utils import timezone

# Librería PDF
from weasyprint import HTML
import tempfile

# Modelos y Formularios del Sistema
from .models import CentroPevi, Usuario
from .forms import UsuarioForm, UsuarioEditarForm
from auditorias.models import ProyectoAuditoria, Empresa
from auditorias.forms import (
    ProyectoForm, ProduccionForm, DocumentoForm, EmpresaForm,
    ElectricidadForm, GasNaturalForm, CarbonForm, 
    FuelOilForm, BiomasaForm, GasPropanoForm
)

# Decoradores de Seguridad Personalizados
from .decorators import acceso_staff, solo_directivos, solo_lideres, solo_superadmin

# Modelo de Noticias
from web.models import Noticia

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
    
    # Política Default Deny: Empezamos vacío por seguridad
    proyectos = ProyectoAuditoria.objects.none()
    rol_label = "Usuario PEVI"

    # 1. SALUDO DINÁMICO
    hora = timezone.now().hour
    if 5 <= hora < 12: saludo = "Buenos días"
    elif 12 <= hora < 18: saludo = "Buenas tardes"
    else: saludo = "Buenas noches"

    # 2. FILTRADO POR ROL Y CONTEXTO (Lógica Jerárquica)

    # CASO A: Director Nacional con Centro Asignado (Ej: César Acevedo)
    # Prioridad: Mostrar operación de su Centro en el día a día.
    if user.rol == 'DIRECTOR_NACIONAL' and user.centro_pevi:
        proyectos = ProyectoAuditoria.objects.filter(centro=user.centro_pevi)
        rol_label = f"Director Nacional / Centro {user.centro_pevi.nombre}"

    # CASO B: Superadmin o Director Nacional "Puro" (Sin centro específico)
    # Prioridad: Visión de Dios (Todo el país)
    elif user.is_superuser or user.rol == 'DIRECTOR_NACIONAL':
        proyectos = ProyectoAuditoria.objects.all()
        rol_label = "Administración Nacional Consolidada"

    # CASO C: Director de Centro Estándar
    elif user.rol == 'DIRECTOR_CENTRO':
        if user.centro_pevi:
            proyectos = ProyectoAuditoria.objects.filter(centro=user.centro_pevi)
            rol_label = f"Dirección {user.centro_pevi.nombre}"
        else:
            rol_label = "Director sin Centro Asignado"

    # CASO D: Profesor Líder
    elif user.rol == 'PROFESOR':
        proyectos = ProyectoAuditoria.objects.filter(lider_proyecto=user)
        rol_label = "Líder de Proyectos"

    # CASO E: Estudiante / Ingeniero
    elif user.rol == 'ESTUDIANTE':
        proyectos = ProyectoAuditoria.objects.filter(equipo=user)
        rol_label = "Ingeniero Junior / Estudiante"

    # 3. CÁLCULO DE KPIs (Sobre la vista filtrada)
    total_proyectos = proyectos.count()
    activos = proyectos.filter(estado='EJECUCION').count()
    
    # Suma rápida de energía usando el helper del modelo
    total_kwh = sum([p.get_total_kwh() for p in proyectos]) 

    # 4. CONTEXTO PARA EL TEMPLATE
    context = {
        'lista_proyectos': proyectos.order_by('-updated_at')[:10], # Top 10 recientes
        'kpi_total': total_proyectos,
        'kpi_activos': activos,
        'kpi_energia': int(total_kwh),
        'saludo': saludo,
        'rol_label': rol_label,
        
        # Flags para definir qué diseño mostrar (Ejecutivo vs Operativo)
        # Nota: Nacionales y Directores ven el diseño Ejecutivo (Tarjetas de colores)
        'es_directivo': user.rol in ['DIRECTOR_CENTRO', 'DIRECTOR_NACIONAL'] or user.is_superuser,
        'es_operativo': user.rol in ['PROFESOR', 'ESTUDIANTE'],
    }
    
    return render(request, 'gestion/dashboard.html', context)

@login_required
@acceso_staff
def lista_proyectos(request):
    """
    Listado de auditorías con filtros avanzados.
    AJUSTE: Incluye filtro rápido para "Mis Proyectos" en roles directivos.
    """
    user = request.user
    
    # Inicialización
    proyectos = ProyectoAuditoria.objects.none()
    opciones_centros = []
    opciones_lideres = []
    es_vista_nacional = False
    titulo_vista = "Gestión de Proyectos"

    # 1. DEFINICIÓN DE PERMISOS (SCOPE)
    
    # CASO A: Es Nacional (Puro o Híbrido) -> VE TODO
    if user.is_superuser or user.rol == 'DIRECTOR_NACIONAL':
        proyectos = ProyectoAuditoria.objects.select_related('empresa', 'centro', 'lider_proyecto').all()
        
        opciones_centros = CentroPevi.objects.filter(activo=True).order_by('nombre')
        
        # MEJORA: Traemos a TODOS los que tengan proyectos asignados (incluyendo al mismo Director Nacional)
        opciones_lideres = Usuario.objects.filter(proyectos_liderados__isnull=False).distinct().order_by('first_name')
        
        es_vista_nacional = True
        titulo_vista = "Portafolio Nacional de Proyectos"

    # CASO B: Director de Centro
    elif user.rol == 'DIRECTOR_CENTRO':
        if user.centro_pevi:
            proyectos = ProyectoAuditoria.objects.filter(centro=user.centro_pevi).select_related('empresa', 'lider_proyecto')
            # Líderes locales que tengan proyectos
            opciones_lideres = Usuario.objects.filter(centro_pevi=user.centro_pevi, proyectos_liderados__isnull=False).distinct()
            
        es_vista_nacional = False
        titulo_vista = f"Proyectos {user.centro_pevi.nombre}"
        
    # CASO C: Profesor
    elif user.rol == 'PROFESOR':
        proyectos = ProyectoAuditoria.objects.filter(lider_proyecto=user).select_related('empresa')
        es_vista_nacional = False
        titulo_vista = "Mis Proyectos Liderados"
        
    # CASO D: Estudiante
    elif user.rol == 'ESTUDIANTE':
        proyectos = ProyectoAuditoria.objects.filter(equipo=user).select_related('empresa')
        es_vista_nacional = False
        titulo_vista = "Mis Asignaciones"

    # 2. PROCESAMIENTO DE FILTROS
    filtro_q = request.GET.get('q')
    filtro_estado = request.GET.get('estado')
    filtro_fase = request.GET.get('fase')
    filtro_lider = request.GET.get('lider')
    filtro_centro = request.GET.get('centro')

    if filtro_q:
        proyectos = proyectos.filter(Q(nombre_proyecto__icontains=filtro_q) | Q(empresa__razon_social__icontains=filtro_q))

    if filtro_estado:
        proyectos = proyectos.filter(estado=filtro_estado)

    if filtro_fase:
        proyectos = proyectos.filter(fase=filtro_fase)

    # Filtro Líder (Funciona también para filtrarse a sí mismo)
    if filtro_lider and (user.es_directivo or user.is_superuser):
        proyectos = proyectos.filter(lider_proyecto_id=filtro_lider)

    if filtro_centro and es_vista_nacional:
        proyectos = proyectos.filter(centro_id=filtro_centro)

    # 3. CONTEXTO
    context = {
        'proyectos': proyectos.order_by('-updated_at'),
        'page_subtitle': titulo_vista,
        'opciones_centros': opciones_centros,
        'opciones_lideres': opciones_lideres,
        'es_vista_nacional': es_vista_nacional,
        
        'filtro_actual_q': filtro_q or '',
        'filtro_actual_estado': filtro_estado or '',
        'filtro_actual_fase': filtro_fase or '',
        'filtro_actual_lider': int(filtro_lider) if filtro_lider else '',
        'filtro_actual_centro': int(filtro_centro) if filtro_centro else '',
    }

    return render(request, 'gestion/lista_proyectos.html', context)

# ==============================================================================
#  2. GESTIÓN ADMINISTRATIVA (Empresas y Equipo)
#  Seguridad: Solo Directores y Superadmin
# ==============================================================================

@login_required
@solo_lideres
def lista_empresas(request):
    user = request.user

    # AISLAMIENTO DE CENTROS: Cada centro solo ve sus empresas
    if user.is_superuser or user.rol == 'DIRECTOR_NACIONAL':
        empresas = Empresa.objects.all().order_by('razon_social')
    elif user.centro_pevi:
        empresas = Empresa.objects.filter(centro=user.centro_pevi).order_by('razon_social')
    else:
        empresas = Empresa.objects.none()

    return render(request, 'gestion/lista_empresas.html', {'empresas': empresas})

@login_required
@solo_lideres
def crear_empresa(request):
    if request.method == 'POST':
        form = EmpresaForm(request.POST, user=request.user)
        if form.is_valid():
            empresa = form.save(commit=False)
            # AISLAMIENTO: Asignar centro del creador si no viene del formulario
            if not empresa.centro and request.user.centro_pevi:
                empresa.centro = request.user.centro_pevi
            empresa.save()
            messages.success(request, "Empresa registrada exitosamente.")
            return redirect('lista_empresas')
    else:
        form = EmpresaForm(user=request.user)
    return render(request, 'gestion/empresa_form.html', {'form': form, 'titulo': 'Registrar Empresa'})


@login_required
@solo_lideres
def editar_empresa(request, empresa_id):
    empresa = get_object_or_404(Empresa, id=empresa_id)

    # Validar acceso: Solo puede editar si es del mismo centro, nacional o superadmin
    if not request.user.is_superuser and request.user.rol != 'DIRECTOR_NACIONAL':
        if empresa.centro != request.user.centro_pevi:
            raise PermissionDenied("No tienes permiso para editar esta empresa.")

    if request.method == 'POST':
        form = EmpresaForm(request.POST, instance=empresa, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f"Empresa '{empresa.razon_social}' actualizada.")
            return redirect('lista_empresas')
    else:
        form = EmpresaForm(instance=empresa, user=request.user)

    return render(request, 'gestion/empresa_form.html', {
        'form': form,
        'titulo': f'Editar: {empresa.razon_social}',
        'empresa': empresa
    })


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

            # VALIDACIÓN DE AISLAMIENTO: Verificar que líder sea del mismo centro
            if not request.user.is_superuser and request.user.rol != 'DIRECTOR_NACIONAL':
                lider = form.cleaned_data.get('lider_proyecto')
                if lider and lider.centro_pevi != request.user.centro_pevi:
                    messages.error(request, "No puede asignar un líder de otro centro.")
                    return render(request, 'gestion/proyecto_form.html', {'form': form, 'titulo': 'Nuevo Proyecto'})

            proyecto.save()

            # VALIDACIÓN DE AISLAMIENTO: Verificar que equipo sea del mismo centro
            if not request.user.is_superuser and request.user.rol != 'DIRECTOR_NACIONAL':
                equipo = form.cleaned_data.get('equipo')
                if equipo:
                    for miembro in equipo:
                        if miembro.centro_pevi != request.user.centro_pevi:
                            proyecto.delete()  # Rollback
                            messages.error(request, f"El usuario {miembro.get_full_name()} no pertenece a su centro.")
                            return render(request, 'gestion/proyecto_form.html', {'form': form, 'titulo': 'Nuevo Proyecto'})

            form.save_m2m()  # Guardar equipo
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
    es_nacional = request.user.is_superuser or request.user.rol == 'DIRECTOR_NACIONAL'

    if not (es_propietario or es_director_suyo or es_nacional):
        raise PermissionDenied("Solo el líder o director pueden editar la estructura del proyecto.")

    if request.method == 'POST':
        form = ProyectoForm(request.POST, instance=proyecto, user=request.user)
        if form.is_valid():
            # VALIDACIÓN DE AISLAMIENTO: Verificar que líder y equipo sean del mismo centro
            if not es_nacional:
                lider = form.cleaned_data.get('lider_proyecto')
                if lider and lider.centro_pevi != request.user.centro_pevi:
                    messages.error(request, "No puede asignar un líder de otro centro.")
                    return render(request, 'gestion/proyecto_form.html', {'form': form, 'titulo': 'Editar Proyecto'})

                equipo = form.cleaned_data.get('equipo')
                if equipo:
                    for miembro in equipo:
                        if miembro.centro_pevi != request.user.centro_pevi:
                            messages.error(request, f"El usuario {miembro.get_full_name()} no pertenece a su centro.")
                            return render(request, 'gestion/proyecto_form.html', {'form': form, 'titulo': 'Editar Proyecto'})

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
    chart_data_emisiones = []
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
                chart_data_energia.append(int(energia_fuente))
                chart_data_costos.append(int(fuente.costo_total_anual))
                chart_data_emisiones.append(round(fuente.emisiones_totales, 2))
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
        'kpi_emisiones': int(total_emisiones),
        'kpi_energia': int(total_energia),
        'kpi_costo': int(total_costo),
        'kpi_ides': round(indicador_ides, 4),
        'kpi_elec_kwh': int(total_kwh_electrico),
        'kpi_term_mbtu': round(mbtu_termico, 2),

        # Datos Gráficos JSON
        'chart_labels': json.dumps(chart_labels),
        'chart_data_energia': json.dumps(chart_data_energia),
        'chart_data_costos': json.dumps(chart_data_costos),
        'chart_data_emisiones': json.dumps(chart_data_emisiones),
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
        'tipo_energia': tipo_energia,  # Para JS: carbon, fuel_oil, gas_propano, etc.
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


@login_required
@solo_lideres # Solo Directores y Profesores pueden cambiar estados
def cambiar_estado_proyecto(request, proyecto_id, nuevo_estado):
    """
    Cambia el ciclo de vida del proyecto:
    BORRADOR -> EJECUCION -> FINALIZADO
    """
    proyecto = get_object_or_404(ProyectoAuditoria, id=proyecto_id)
    
    # Validación de seguridad extra (Propiedad)
    if not verificar_acceso_proyecto(request.user, proyecto):
        raise PermissionDenied("No tienes permiso sobre este proyecto.")

    # Validar que el estado sea uno de los permitidos
    estados_validos = ['BORRADOR', 'EJECUCION', 'FINALIZADO']
    
    if nuevo_estado in estados_validos:
        proyecto.estado = nuevo_estado
        proyecto.save()
        
        # Mensajes de feedback según el estado
        if nuevo_estado == 'EJECUCION':
            messages.success(request, "¡Proyecto activado! Ahora está En Ejecución.")
        elif nuevo_estado == 'FINALIZADO':
            messages.success(request, "Proyecto Finalizado y Cerrado exitosamente.")
        else:
            messages.info(request, "Estado del proyecto actualizado.")

    return redirect('detalle_proyecto', proyecto_id=proyecto.id)


# ==============================================================================
#  6. PANEL DE CONTROL SUPERADMIN
#  Seguridad: Solo Superusuarios (is_superuser=True)
# ==============================================================================

@login_required
@solo_superadmin
def control_panel(request):
    """
    Dashboard principal del Panel de Control del Superadmin.
    Muestra estadísticas globales y accesos rápidos.
    """
    context = {
        'total_centros': CentroPevi.objects.count(),
        'centros_activos': CentroPevi.objects.filter(activo=True).count(),
        'total_usuarios': Usuario.objects.count(),
        'total_noticias': Noticia.objects.count(),
        'total_proyectos': ProyectoAuditoria.objects.count(),
        'total_empresas': Empresa.objects.count(),

        # Últimos registros
        'ultimos_centros': CentroPevi.objects.order_by('-id')[:5],
        'ultimos_usuarios': Usuario.objects.order_by('-date_joined')[:5],
        'ultimas_noticias': Noticia.objects.order_by('-fecha_publicacion')[:5],
    }
    return render(request, 'control/panel.html', context)


# --- CRUD CENTROS PEVI ---

@login_required
@solo_superadmin
def control_centros_lista(request):
    """Lista todos los Centros PEVI."""
    centros = CentroPevi.objects.all().order_by('nombre')
    return render(request, 'control/centros_lista.html', {'centros': centros})


@login_required
@solo_superadmin
def control_centro_crear(request):
    """Crea un nuevo Centro PEVI."""
    from .forms import CentroPeviForm

    if request.method == 'POST':
        form = CentroPeviForm(request.POST, request.FILES)
        if form.is_valid():
            centro = form.save()
            messages.success(request, f"Centro '{centro.nombre}' creado exitosamente.")
            return redirect('control_centros_lista')
    else:
        form = CentroPeviForm()

    return render(request, 'control/centro_form.html', {
        'form': form,
        'titulo': 'Crear Centro PEVI',
        'accion': 'Crear'
    })


@login_required
@solo_superadmin
def control_centro_editar(request, centro_id):
    """Edita un Centro PEVI existente."""
    from .forms import CentroPeviForm

    centro = get_object_or_404(CentroPevi, id=centro_id)

    if request.method == 'POST':
        form = CentroPeviForm(request.POST, request.FILES, instance=centro)
        if form.is_valid():
            form.save()
            messages.success(request, f"Centro '{centro.nombre}' actualizado.")
            return redirect('control_centros_lista')
    else:
        form = CentroPeviForm(instance=centro)

    return render(request, 'control/centro_form.html', {
        'form': form,
        'titulo': f'Editar: {centro.nombre_corto or centro.nombre}',
        'accion': 'Guardar Cambios',
        'centro': centro
    })


@login_required
@solo_superadmin
def control_centro_eliminar(request, centro_id):
    """Elimina un Centro PEVI (con confirmación POST)."""
    centro = get_object_or_404(CentroPevi, id=centro_id)

    if request.method == 'POST':
        nombre = centro.nombre
        centro.delete()
        messages.success(request, f"Centro '{nombre}' eliminado permanentemente.")
        return redirect('control_centros_lista')

    return render(request, 'control/confirmar_eliminar.html', {
        'objeto': centro,
        'tipo': 'Centro PEVI',
        'nombre': centro.nombre,
        'url_cancelar': 'control_centros_lista'
    })


# --- CRUD USUARIOS ---

@login_required
@solo_superadmin
def control_usuarios_lista(request):
    """Lista todos los usuarios del sistema."""
    usuarios = Usuario.objects.select_related('centro_pevi').order_by('-date_joined')
    return render(request, 'control/usuarios_lista.html', {'usuarios': usuarios})


@login_required
@solo_superadmin
def control_usuario_crear(request):
    """Crea un nuevo usuario con rol y centro asignados."""
    from .forms import UsuarioAdminForm

    if request.method == 'POST':
        form = UsuarioAdminForm(request.POST)
        if form.is_valid():
            usuario = form.save(commit=False)
            usuario.set_password(form.cleaned_data['password'])
            usuario.save()
            messages.success(request, f"Usuario '{usuario.username}' creado exitosamente.")
            return redirect('control_usuarios_lista')
    else:
        form = UsuarioAdminForm()

    return render(request, 'control/usuario_form.html', {
        'form': form,
        'titulo': 'Crear Usuario',
        'accion': 'Crear'
    })


@login_required
@solo_superadmin
def control_usuario_editar(request, usuario_id):
    """Edita un usuario existente."""
    from .forms import UsuarioAdminEditForm

    usuario = get_object_or_404(Usuario, id=usuario_id)

    if request.method == 'POST':
        form = UsuarioAdminEditForm(request.POST, instance=usuario)
        if form.is_valid():
            usuario = form.save(commit=False)
            # Si se proporciona nueva contraseña
            nueva_password = form.cleaned_data.get('nueva_password')
            if nueva_password:
                usuario.set_password(nueva_password)
            usuario.save()
            messages.success(request, f"Usuario '{usuario.username}' actualizado.")
            return redirect('control_usuarios_lista')
    else:
        form = UsuarioAdminEditForm(instance=usuario)

    return render(request, 'control/usuario_form.html', {
        'form': form,
        'titulo': f'Editar: {usuario.username}',
        'accion': 'Guardar Cambios',
        'usuario': usuario
    })


@login_required
@solo_superadmin
def control_usuario_eliminar(request, usuario_id):
    """Elimina un usuario (con confirmación POST)."""
    usuario = get_object_or_404(Usuario, id=usuario_id)

    # Prevenir auto-eliminación
    if usuario == request.user:
        messages.error(request, "No puedes eliminarte a ti mismo.")
        return redirect('control_usuarios_lista')

    if request.method == 'POST':
        nombre = usuario.username
        usuario.delete()
        messages.success(request, f"Usuario '{nombre}' eliminado permanentemente.")
        return redirect('control_usuarios_lista')

    return render(request, 'control/confirmar_eliminar.html', {
        'objeto': usuario,
        'tipo': 'Usuario',
        'nombre': f"{usuario.get_full_name()} ({usuario.username})",
        'url_cancelar': 'control_usuarios_lista'
    })


# --- CRUD NOTICIAS ---

@login_required
@solo_superadmin
def control_noticias_lista(request):
    """Lista todas las noticias."""
    noticias = Noticia.objects.order_by('-fecha_publicacion')
    return render(request, 'control/noticias_lista.html', {'noticias': noticias})


@login_required
@solo_superadmin
def control_noticia_crear(request):
    """Crea una nueva noticia."""
    from .forms import NoticiaAdminForm

    if request.method == 'POST':
        form = NoticiaAdminForm(request.POST, request.FILES)
        if form.is_valid():
            noticia = form.save(commit=False)
            noticia.autor = request.user
            noticia.save()
            messages.success(request, f"Noticia '{noticia.titulo}' publicada.")
            return redirect('control_noticias_lista')
    else:
        form = NoticiaAdminForm()

    return render(request, 'control/noticia_form.html', {
        'form': form,
        'titulo': 'Crear Noticia',
        'accion': 'Publicar'
    })


@login_required
@solo_superadmin
def control_noticia_editar(request, noticia_id):
    """Edita una noticia existente."""
    from .forms import NoticiaAdminForm

    noticia = get_object_or_404(Noticia, id=noticia_id)

    if request.method == 'POST':
        form = NoticiaAdminForm(request.POST, request.FILES, instance=noticia)
        if form.is_valid():
            form.save()
            messages.success(request, f"Noticia '{noticia.titulo}' actualizada.")
            return redirect('control_noticias_lista')
    else:
        form = NoticiaAdminForm(instance=noticia)

    return render(request, 'control/noticia_form.html', {
        'form': form,
        'titulo': f'Editar: {noticia.titulo[:30]}...',
        'accion': 'Guardar Cambios',
        'noticia': noticia
    })


@login_required
@solo_superadmin
def control_noticia_eliminar(request, noticia_id):
    """Elimina una noticia (con confirmación POST)."""
    noticia = get_object_or_404(Noticia, id=noticia_id)

    if request.method == 'POST':
        titulo = noticia.titulo
        noticia.delete()
        messages.success(request, f"Noticia '{titulo}' eliminada.")
        return redirect('control_noticias_lista')

    return render(request, 'control/confirmar_eliminar.html', {
        'objeto': noticia,
        'tipo': 'Noticia',
        'nombre': noticia.titulo,
        'url_cancelar': 'control_noticias_lista'
    })