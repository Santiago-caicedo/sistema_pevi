from django.core.management.base import BaseCommand
from auditorias.models import GasNatural, CarbonMineral, FuelOil, Biomasa, GasPropano


class Command(BaseCommand):
    help = 'Recalcula consumo_anual_kwh para todos los registros de combustibles existentes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Muestra los cambios sin guardarlos',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('MODO DRY-RUN: No se guardarán cambios'))

        modelos = [
            ('Gas Natural', GasNatural),
            ('Carbón Mineral', CarbonMineral),
            ('Fuel Oil', FuelOil),
            ('Biomasa', Biomasa),
            ('Gas Propano (GLP)', GasPropano),
        ]

        total_actualizados = 0

        for nombre, modelo in modelos:
            registros = modelo.objects.all()
            count = registros.count()

            if count == 0:
                self.stdout.write(f'{nombre}: Sin registros')
                continue

            self.stdout.write(f'\n{nombre}: {count} registro(s)')
            self.stdout.write('-' * 50)

            for registro in registros:
                valor_anterior = registro.consumo_anual_kwh

                # El método save() ahora tiene la lógica correcta de conversión
                if not dry_run:
                    registro.save()
                    valor_nuevo = registro.consumo_anual_kwh
                else:
                    # Calculamos sin guardar para mostrar el cambio
                    valor_nuevo = self._calcular_kwh(registro)

                cambio = valor_nuevo - valor_anterior if valor_anterior else valor_nuevo
                porcentaje = (cambio / valor_anterior * 100) if valor_anterior and valor_anterior != 0 else 0

                self.stdout.write(
                    f'  ID {registro.id} ({registro.proyecto}): '
                    f'{valor_anterior:,.0f} → {valor_nuevo:,.0f} kWh '
                    f'({porcentaje:+.1f}%)'
                )
                total_actualizados += 1

        self.stdout.write('\n' + '=' * 50)
        if dry_run:
            self.stdout.write(self.style.WARNING(f'Se actualizarían {total_actualizados} registro(s)'))
            self.stdout.write(self.style.WARNING('Ejecuta sin --dry-run para aplicar cambios'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Se actualizaron {total_actualizados} registro(s)'))

    def _calcular_kwh(self, registro):
        """Calcula kWh sin guardar (para dry-run)"""
        factor_unidad = 1.0
        factor_energia = 1.0

        model_name = registro._meta.model_name

        if model_name == 'carbonmineral':
            factor_unidad = 1000.0   # Ton → kg
            factor_energia = 1000.0  # MJ → kJ
        elif model_name == 'biomasa':
            factor_unidad = 1000.0   # Ton → kg
            factor_energia = 1.0     # kJ (ya está en kJ)
        elif model_name == 'fueloil':
            factor_unidad = 1.0      # Galones
            factor_energia = 1000.0  # MJ → kJ
        elif model_name == 'gaspropano':
            factor_unidad = 1.0      # kg
            factor_energia = 1000.0  # MJ → kJ
        # Gas Natural: m³, kJ/m³ → factores = 1.0

        if registro.consumo_anual_orig and registro.poder_calorifico:
            energia_kj = (registro.consumo_anual_orig * factor_unidad) * registro.poder_calorifico * factor_energia
            return energia_kj / 3600

        return 0
