import re

from django.core.management.base import BaseCommand
from django.db import transaction

from auditorias.models import ProyectoAuditoria
from gestion.logger import logger_actividad, _guardar_en_db
from gestion.models import RegistroActividad


RELACIONES_ENERGIA = [
    'electricidad_related', 'gasnatural_related', 'carbonmineral_related',
    'fueloil_related', 'biomasa_related', 'gaspropano_related',
]


def normalizar(texto):
    return re.sub(r'\s+', ' ', (texto or '').strip().lower())


def resumen_datos(proyecto):
    """Cuenta los datos cargados en un proyecto (para decidir si es seguro borrarlo)."""
    fuentes = sum(getattr(proyecto, rel).count() for rel in RELACIONES_ENERGIA)
    return {
        'fuentes': fuentes,
        'opm': proyecto.oportunidades_mejora.count(),
        'docs': proyecto.documentos.count(),
        'produccion': bool(proyecto.produccion_total),
    }


def tiene_datos(datos):
    return bool(datos['fuentes'] or datos['opm'] or datos['docs'] or datos['produccion'])


def creador_de(proyecto):
    """Usuario que creó el proyecto, según la bitácora de actividad."""
    registro = (
        RegistroActividad.objects
        .filter(accion=RegistroActividad.ACCION_CREAR, modelo_afectado='Proyecto', objeto_id=proyecto.id)
        .select_related('usuario')
        .first()
    )
    return registro.usuario if registro else None


class Command(BaseCommand):
    help = (
        'Detecta proyectos duplicados (misma empresa + mismo nombre). Por defecto solo '
        'reporta. Con --aplicar elimina los duplicados VACÍOS y agrega al creador '
        '(profesor) al equipo del proyecto que se conserva.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--aplicar',
            action='store_true',
            help='Elimina los duplicados sin datos (por defecto solo muestra el reporte)',
        )

    def handle(self, *args, **options):
        aplicar = options['aplicar']

        if not aplicar:
            self.stdout.write(self.style.WARNING('MODO REPORTE: No se modificará nada (usar --aplicar para corregir)'))

        grupos = {}
        proyectos = ProyectoAuditoria.objects.select_related('empresa', 'lider_proyecto', 'centro').order_by('created_at')
        for p in proyectos:
            grupos.setdefault((p.empresa_id, normalizar(p.nombre_proyecto)), []).append(p)

        duplicados = [g for g in grupos.values() if len(g) > 1]
        if not duplicados:
            self.stdout.write(self.style.SUCCESS('No se encontraron proyectos duplicados.'))
            return

        total_eliminados = 0
        total_revisar = 0

        for grupo in duplicados:
            filas = [(p, resumen_datos(p)) for p in grupo]
            # Conservar el que tenga más datos; en empate, el más antiguo
            conservar = max(filas, key=lambda f: (tiene_datos(f[1]), sum(f[1].values()), -f[0].created_at.timestamp()))[0]

            primero = grupo[0]
            self.stdout.write('\n' + '=' * 70)
            self.stdout.write(f'{primero.empresa.razon_social} | "{primero.nombre_proyecto}" | {len(grupo)} copias')
            self.stdout.write('-' * 70)

            for p, datos in filas:
                creador = creador_de(p)
                if p == conservar:
                    marca = self.style.SUCCESS('CONSERVAR')
                elif tiene_datos(datos):
                    marca = self.style.ERROR('REVISAR  ')
                else:
                    marca = self.style.WARNING('ELIMINAR ')
                self.stdout.write(
                    f'  [{marca}] ID {p.id} | creado {p.created_at:%Y-%m-%d %H:%M} | {p.get_estado_display()} | '
                    f'líder: {p.lider_proyecto.username if p.lider_proyecto else "-"} | '
                    f'creador: {creador.username if creador else "?"} | '
                    f'fuentes: {datos["fuentes"]}, OPM: {datos["opm"]}, docs: {datos["docs"]}, '
                    f'producción: {"sí" if datos["produccion"] else "no"}'
                )

            a_eliminar = [p for p, datos in filas if p != conservar and not tiene_datos(datos)]
            total_revisar += sum(1 for p, datos in filas if p != conservar and tiene_datos(datos))

            if not aplicar:
                total_eliminados += len(a_eliminar)
                continue

            with transaction.atomic():
                # El profesor que creó las copias queda en el equipo del proyecto conservado
                for p in grupo:
                    creador = creador_de(p)
                    if (creador and creador.rol == 'PROFESOR' and creador != conservar.lider_proyecto
                            and not conservar.equipo.filter(id=creador.id).exists()):
                        conservar.equipo.add(creador)
                        self.stdout.write(f'  + {creador.username} agregado al equipo del proyecto {conservar.id}')

                for p in a_eliminar:
                    repr_p = f'{p.nombre_proyecto} - {p.empresa.razon_social} (duplicado de {conservar.id})'
                    proyecto_id = p.id
                    p.delete()
                    logger_actividad.info(f'ELIMINAR Proyecto | ID: {proyecto_id} | {repr_p} | Comando proyectos_duplicados')
                    _guardar_en_db(
                        tipo='ACTIVIDAD', accion='ELIMINAR', modelo='Proyecto',
                        objeto_id=proyecto_id, objeto_repr=repr_p,
                        descripcion=f'Eliminado por comando proyectos_duplicados: {repr_p}',
                    )
                    total_eliminados += 1

        self.stdout.write('\n' + '=' * 70)
        self.stdout.write(f'Grupos duplicados: {len(duplicados)}')
        verbo = 'Eliminados' if aplicar else 'Se eliminarían'
        self.stdout.write(self.style.SUCCESS(f'{verbo}: {total_eliminados} proyecto(s) vacío(s)'))
        if total_revisar:
            self.stdout.write(self.style.ERROR(
                f'Para revisar a mano: {total_revisar} copia(s) con datos cargados (no se tocan)'
            ))
