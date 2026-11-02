from django.core.management.base import BaseCommand, CommandError

from auditorias.management.commands.proyectos_duplicados import resumen_datos, tiene_datos, creador_de
from auditorias.models import ProyectoAuditoria
from gestion.logger import logger_actividad, _guardar_en_db


class Command(BaseCommand):
    help = (
        'Elimina un proyecto por ID. Por defecto solo muestra lo que se borraría; '
        'usar --confirmar para borrar. Se niega a borrar proyectos con datos cargados.'
    )

    def add_arguments(self, parser):
        parser.add_argument('proyecto_id', type=int, help='ID del proyecto a eliminar')
        parser.add_argument(
            '--confirmar',
            action='store_true',
            help='Elimina el proyecto (por defecto solo muestra el reporte)',
        )

    def handle(self, *args, **options):
        proyecto_id = options['proyecto_id']

        try:
            p = ProyectoAuditoria.objects.select_related('empresa', 'lider_proyecto').get(id=proyecto_id)
        except ProyectoAuditoria.DoesNotExist:
            raise CommandError(f'No existe el proyecto con ID {proyecto_id}.')

        datos = resumen_datos(p)
        creador = creador_de(p)

        self.stdout.write(f'ID {p.id} | "{p.nombre_proyecto}" | {p.empresa.razon_social}')
        self.stdout.write(
            f'  creado {p.created_at:%Y-%m-%d %H:%M} | {p.get_estado_display()} | '
            f'líder: {p.lider_proyecto.username if p.lider_proyecto else "-"} | '
            f'creador: {creador.username if creador else "?"}'
        )
        self.stdout.write(
            f'  fuentes: {datos["fuentes"]}, OPM: {datos["opm"]}, docs: {datos["docs"]}, '
            f'producción: {"sí" if datos["produccion"] else "no"}'
        )

        if tiene_datos(datos):
            raise CommandError('El proyecto tiene datos cargados: no se elimina por seguridad.')

        if not options['confirmar']:
            self.stdout.write(self.style.WARNING('MODO REPORTE: no se eliminó nada (usar --confirmar para borrar)'))
            return

        repr_p = f'{p.nombre_proyecto} - {p.empresa.razon_social}'
        p.delete()
        logger_actividad.info(f'ELIMINAR Proyecto | ID: {proyecto_id} | {repr_p} | Comando eliminar_proyecto')
        _guardar_en_db(
            tipo='ACTIVIDAD', accion='ELIMINAR', modelo='Proyecto',
            objeto_id=proyecto_id, objeto_repr=repr_p,
            descripcion=f'Eliminado por comando eliminar_proyecto: {repr_p}',
        )
        self.stdout.write(self.style.SUCCESS(f'Proyecto {proyecto_id} eliminado.'))
