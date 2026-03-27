from django.core.management.base import BaseCommand
from auditorias.models import ProyectoAuditoria


class Command(BaseCommand):
    help = 'Detecta proyectos donde el centro del proyecto no coincide con el centro de la empresa'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Corrige los proyectos asignándoles el centro de su empresa',
        )

    def handle(self, *args, **options):
        fix = options['fix']

        proyectos = ProyectoAuditoria.objects.select_related(
            'empresa', 'empresa__centro', 'centro', 'lider_proyecto'
        ).exclude(empresa__centro=None).exclude(centro=None)

        inconsistentes = []
        for p in proyectos:
            if p.empresa.centro_id != p.centro_id:
                inconsistentes.append(p)

        if not inconsistentes:
            self.stdout.write(self.style.SUCCESS('No se encontraron inconsistencias. Todo OK.'))
            return

        self.stdout.write(self.style.WARNING(
            f'Se encontraron {len(inconsistentes)} proyecto(s) con centro inconsistente:\n'
        ))

        for p in inconsistentes:
            self.stdout.write(
                f'  ID: {p.id} | {p.nombre_proyecto[:50]}\n'
                f'    Centro proyecto:  {p.centro.nombre}\n'
                f'    Centro empresa:   {p.empresa.centro.nombre}\n'
                f'    Líder:            {p.lider_proyecto.get_full_name() if p.lider_proyecto else "Sin líder"}\n'
                f'    Estado:           {p.estado}\n'
            )

        if fix:
            self.stdout.write('')
            for p in inconsistentes:
                centro_anterior = p.centro.nombre
                p.centro = p.empresa.centro
                p.save(update_fields=['centro'])
                self.stdout.write(self.style.SUCCESS(
                    f'  ID {p.id}: {centro_anterior} → {p.empresa.centro.nombre}'
                ))

            self.stdout.write(self.style.SUCCESS(
                f'\nCorregidos {len(inconsistentes)} proyecto(s).'
            ))
        else:
            self.stdout.write(self.style.NOTICE(
                '\nUsa --fix para corregirlos automáticamente (asigna el centro de la empresa).'
            ))
