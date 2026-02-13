from django.core.management.base import BaseCommand
from auditorias.models import Electricidad, GasNatural, CarbonMineral, FuelOil, Biomasa, GasPropano


class Command(BaseCommand):
    help = 'Recalcula consumo_anual_kwh y emisiones_totales para todos los registros energéticos'

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

        # --- Electricidad (solo emisiones) ---
        self.stdout.write(f'\nElectricidad:')
        self.stdout.write('-' * 50)
        registros_elec = Electricidad.objects.all()

        if registros_elec.count() == 0:
            self.stdout.write('  Sin registros')
        else:
            for registro in registros_elec:
                emisiones_anterior = registro.emisiones_totales
                emisiones_nueva = self._calcular_emisiones_electricidad(registro)

                if not dry_run:
                    registro.save()
                    emisiones_nueva = registro.emisiones_totales

                self.stdout.write(
                    f'  ID {registro.id} ({registro.proyecto}): '
                    f'Emisiones: {emisiones_anterior:,.2f} → {emisiones_nueva:,.2f} TonCO2'
                )

        # --- Combustibles (kWh + emisiones) ---
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
                self.stdout.write(f'\n{nombre}: Sin registros')
                continue

            self.stdout.write(f'\n{nombre}: {count} registro(s)')
            self.stdout.write('-' * 50)

            for registro in registros:
                kwh_anterior = registro.consumo_anual_kwh
                emisiones_anterior = registro.emisiones_totales

                if not dry_run:
                    registro.save()
                    kwh_nuevo = registro.consumo_anual_kwh
                    emisiones_nueva = registro.emisiones_totales
                else:
                    kwh_nuevo = self._calcular_kwh(registro)
                    emisiones_nueva = self._calcular_emisiones_combustible(registro)

                cambio_kwh = kwh_nuevo - kwh_anterior if kwh_anterior else kwh_nuevo
                pct_kwh = (cambio_kwh / kwh_anterior * 100) if kwh_anterior and kwh_anterior != 0 else 0

                self.stdout.write(
                    f'  ID {registro.id} ({registro.proyecto}): '
                    f'kWh: {kwh_anterior:,.0f} → {kwh_nuevo:,.0f} ({pct_kwh:+.1f}%) | '
                    f'Emisiones: {emisiones_anterior:,.2f} → {emisiones_nueva:,.2f} TonCO2'
                )
                total_actualizados += 1

        self.stdout.write('\n' + '=' * 50)
        if dry_run:
            self.stdout.write(self.style.WARNING(f'Se actualizarían {total_actualizados + registros_elec.count()} registro(s)'))
            self.stdout.write(self.style.WARNING('Ejecuta sin --dry-run para aplicar cambios'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Se actualizaron {total_actualizados + registros_elec.count()} registro(s)'))

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

    def _calcular_emisiones_combustible(self, registro):
        """Calcula emisiones TonCO2 para combustibles (para dry-run)"""
        if registro.consumo_anual_orig and registro.factor_emision:
            return (registro.consumo_anual_orig * registro.factor_emision) / 1000
        return 0

    def _calcular_emisiones_electricidad(self, registro):
        """Calcula emisiones TonCO2 para electricidad (para dry-run)"""
        if registro.consumo_anual and registro.factor_emision:
            return (registro.consumo_anual * registro.factor_emision) / 1000
        return 0
