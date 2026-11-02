from datetime import date, timedelta
from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from auditorias.models import Electricidad, Empresa, ProyectoAuditoria
from gestion.models import CentroPevi, RegistroActividad, Usuario


class ProyectosDuplicadosCommandTests(TestCase):

    def setUp(self):
        self.centro = CentroPevi.objects.create(nombre='Centro A', codigo_interno='CA', region='Caribe')
        self.creador = Usuario.objects.create_user('creador', password='x', rol='PROFESOR', centro_pevi=self.centro)
        self.lider = Usuario.objects.create_user('lider', password='x', rol='PROFESOR', centro_pevi=self.centro)
        self.empresa = Empresa.objects.create(
            razon_social='Empresa', nit='900', centro=self.centro, sector_productivo='X',
            direccion='C', ciudad='Cali', contacto_nombre='C', contacto_email='c@t.co', contacto_telefono='1',
        )

    def crear_proyecto(self, nombre='Auditoría Planta 1', minutos=0):
        p = ProyectoAuditoria.objects.create(
            centro=self.centro, empresa=self.empresa, lider_proyecto=self.lider,
            nombre_proyecto=nombre, fecha_inicio=date.today(),
        )
        # created_at es auto_now_add: se ajusta para fijar el orden de creación
        ProyectoAuditoria.objects.filter(id=p.id).update(created_at=timezone.now() + timedelta(minutes=minutos))
        RegistroActividad.objects.create(
            tipo='ACTIVIDAD', accion='CREAR', usuario=self.creador, modelo_afectado='Proyecto', objeto_id=p.id,
        )
        return p

    def agregar_electricidad(self, proyecto):
        Electricidad.objects.create(
            proyecto=proyecto, costo_unitario=1, costo_mensual_promedio=1, costo_total_anual=12,
            factor_emision=0.1, emisiones_totales=1, consumo_mensual=10, consumo_anual=120,
        )

    def ejecutar(self, *args):
        out = StringIO()
        call_command('proyectos_duplicados', *args, stdout=out)
        return out.getvalue()

    def test_reporte_no_modifica_nada(self):
        self.crear_proyecto(minutos=0)
        self.crear_proyecto(minutos=1)

        salida = self.ejecutar()

        self.assertIn('2 copias', salida)
        self.assertEqual(ProyectoAuditoria.objects.count(), 2)

    def test_aplicar_conserva_el_mas_antiguo_y_borra_vacios(self):
        original = self.crear_proyecto(minutos=0)
        self.crear_proyecto(minutos=1)
        self.crear_proyecto(minutos=2)

        self.ejecutar('--aplicar')

        self.assertEqual(list(ProyectoAuditoria.objects.values_list('id', flat=True)), [original.id])

    def test_conserva_la_copia_con_datos_aunque_no_sea_la_mas_antigua(self):
        self.crear_proyecto(minutos=0)
        con_datos = self.crear_proyecto(minutos=1)
        self.agregar_electricidad(con_datos)

        self.ejecutar('--aplicar')

        self.assertEqual(list(ProyectoAuditoria.objects.values_list('id', flat=True)), [con_datos.id])

    def test_no_borra_copias_con_datos(self):
        a = self.crear_proyecto(minutos=0)
        b = self.crear_proyecto(minutos=1)
        self.agregar_electricidad(a)
        self.agregar_electricidad(b)

        salida = self.ejecutar('--aplicar')

        self.assertEqual(ProyectoAuditoria.objects.count(), 2)
        self.assertIn('revisar a mano', salida)

    def test_agrega_creador_al_equipo_del_conservado(self):
        original = self.crear_proyecto(minutos=0)
        self.crear_proyecto(minutos=1)

        self.ejecutar('--aplicar')

        self.assertIn(self.creador, original.equipo.all())

    def test_nombre_con_mayusculas_y_espacios_cuenta_como_duplicado(self):
        self.crear_proyecto('Auditoría Planta 1', minutos=0)
        self.crear_proyecto('  auditoría   planta 1 ', minutos=1)

        self.ejecutar('--aplicar')

        self.assertEqual(ProyectoAuditoria.objects.count(), 1)

    def test_filtro_empresa_no_toca_otras_empresas(self):
        """--empresa inalkem limpia solo esa empresa (ej: DAGMA queda intacta)."""
        inalkem = Empresa.objects.create(
            razon_social='GRUPO INALKEM SAS', nit='901', centro=self.centro, sector_productivo='X',
            direccion='C', ciudad='Cali', contacto_nombre='C', contacto_email='c@t.co', contacto_telefono='1',
        )
        otra_1 = self.crear_proyecto('Fase 4', minutos=0)
        otra_2 = self.crear_proyecto('Fase 4', minutos=1)
        self.empresa = inalkem
        ina_1 = self.crear_proyecto('Evaluación', minutos=0)
        self.crear_proyecto('Evaluación', minutos=1)
        ina_2 = self.crear_proyecto('Evaluación - 2025', minutos=2)
        self.crear_proyecto('Evaluación - 2025', minutos=3)

        self.ejecutar('--aplicar', '--empresa', 'inalkem')

        self.assertEqual(set(ProyectoAuditoria.objects.values_list('id', flat=True)),
                         {otra_1.id, otra_2.id, ina_1.id, ina_2.id})
        self.assertIn(self.creador, ina_1.equipo.all())
        self.assertIn(self.creador, ina_2.equipo.all())

    def test_nombres_distintos_no_son_duplicados(self):
        self.crear_proyecto('Planta 1')
        self.crear_proyecto('Planta 2')

        salida = self.ejecutar('--aplicar')

        self.assertIn('No se encontraron', salida)
        self.assertEqual(ProyectoAuditoria.objects.count(), 2)

    def test_eliminar_proyecto_sin_confirmar_no_borra(self):
        p = self.crear_proyecto()
        out = StringIO()
        call_command('eliminar_proyecto', p.id, stdout=out)
        self.assertIn('MODO REPORTE', out.getvalue())
        self.assertTrue(ProyectoAuditoria.objects.filter(id=p.id).exists())

    def test_eliminar_proyecto_confirmado_borra_y_registra(self):
        p = self.crear_proyecto()
        call_command('eliminar_proyecto', p.id, '--confirmar', stdout=StringIO())
        self.assertFalse(ProyectoAuditoria.objects.filter(id=p.id).exists())
        self.assertTrue(RegistroActividad.objects.filter(
            accion='ELIMINAR', modelo_afectado='Proyecto', objeto_id=p.id,
        ).exists())

    def test_eliminar_proyecto_con_datos_se_niega(self):
        from django.core.management.base import CommandError
        p = self.crear_proyecto()
        self.agregar_electricidad(p)
        with self.assertRaises(CommandError):
            call_command('eliminar_proyecto', p.id, '--confirmar', stdout=StringIO())
        self.assertTrue(ProyectoAuditoria.objects.filter(id=p.id).exists())

    def test_eliminar_proyecto_inexistente(self):
        from django.core.management.base import CommandError
        with self.assertRaises(CommandError):
            call_command('eliminar_proyecto', 99999, stdout=StringIO())

    def test_registra_eliminacion_en_bitacora(self):
        self.crear_proyecto(minutos=0)
        duplicado = self.crear_proyecto(minutos=1)

        self.ejecutar('--aplicar')

        self.assertTrue(RegistroActividad.objects.filter(
            accion='ELIMINAR', modelo_afectado='Proyecto', objeto_id=duplicado.id,
        ).exists())
