from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from auditorias.models import ProyectoAuditoria

# @login_required  <-- Lo descomentaremos cuando configuremos el login, por ahora déjalo comentado para probar rápido
def dashboard(request):
    """
    Panel principal. Muestra KPIs y lista de proyectos recientes.
    """
    # Por ahora traemos todos, luego filtraremos por usuario
    proyectos = ProyectoAuditoria.objects.all().order_by('-created_at')[:5]
    
    context = {
        'total_proyectos': ProyectoAuditoria.objects.count(),
        'proyectos_activos': ProyectoAuditoria.objects.filter(estado='EJECUCION').count(),
        'lista_proyectos': proyectos
    }
    return render(request, 'gestion/dashboard.html', context)