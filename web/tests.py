"""Tests de la página pública de resultados (boletín de impacto)."""
import json
from datetime import date

from django.test import TestCase
from django.urls import reverse

from auditorias.models import Electricidad, Empresa, ProyectoAuditoria
from gestion.models import CentroPevi


class ResultadosPublicosTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.caribe = CentroPevi.objects.create(
            nombre='Universidad del Atlántico', nombre_corto='UA', codigo_interno='UA',
            region='Caribe', ciudad='Barranquilla', latitud=10.98, longitud=-74.80)
        cls.andina = CentroPevi.objects.create(
            nombre='Universidad Tecnológica de Pereira', nombre_corto='UTP', codigo_interno='UTP',
            region='Andina', ciudad='Pereira')  # sin coordenadas

        def empresa(nit, centro, sector):
            return Empresa.objects.create(
                razon_social=f'Empresa {nit}', nit=nit, centro=centro, sector_productivo=sector,
                direccion='C', ciudad='X', contacto_nombre='C', contacto_email='c@t.co', contacto_telefono='1')

        cls.e1 = empresa('1', cls.caribe, 'Alimentos')
        cls.e2 = empresa('2', cls.andina, 'Textil')
        p1 = ProyectoAuditoria.objects.create(centro=cls.caribe, empresa=cls.e1, nombre_proyecto='A',
                                              fecha_inicio=date(2025, 3, 1))
        ProyectoAuditoria.objects.create(centro=cls.andina, empresa=cls.e2, nombre_proyecto='B',
                                         fecha_inicio=date(2026, 3, 1))
        Electricidad.objects.create(
            proyecto=p1, costo_unitario=1, costo_mensual_promedio=1, costo_total_anual=12,
            factor_emision=0.1, emisiones_totales=40, consumo_mensual=1000, consumo_anual=250000)

    def get(self, **params):
        return self.client.get(reverse('resultados_public'), params)

    def datos(self, r):
        html = r.content.decode()
        inicio = html.index('<script id="rb-datos" type="application/json">') + len('<script id="rb-datos" type="application/json">')
        return json.loads(html[inicio:html.index('</script>', inicio)])

    def test_renderiza_cifras_nacionales(self):
        r = self.get()
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['total_proyectos'], 2)
        self.assertEqual(r.context['total_energia_mwh'], 250)
        self.assertEqual(r.context['sectores_unicos'], 2)
        self.assertContains(r, 'Resultados del Programa PEVI')

    def test_matriz_energetica(self):
        matriz = {f['nombre']: f for f in self.get().context['matriz_energia']}
        self.assertEqual(matriz['Electricidad']['mwh'], 250)
        self.assertAlmostEqual(matriz['Electricidad']['pct'], 100.0)
        self.assertEqual(matriz['Biomasa']['mwh'], 0)

    def test_filtros_aplican_a_todas_las_series(self):
        r = self.get(region='Caribe')
        self.assertEqual(r.context['total_proyectos'], 1)
        self.assertEqual([s['etiqueta'] for s in r.context['serie_sectores']], ['Alimentos'])
        self.assertEqual([s['etiqueta'] for s in r.context['serie_anual']], ['2025'])
        self.assertEqual(r.context['sectores_unicos'], 1)

    def test_mapa_solo_centros_con_coordenadas_y_tabla_con_todos(self):
        r = self.get()
        self.assertEqual([c['sigla'] for c in self.datos(r)['mapa']], ['UA'])
        self.assertEqual({c['sigla'] for c in r.context['centros_tabla']}, {'UA', 'UTP'})

    def test_seleccion_sin_resultados_muestra_aviso(self):
        r = self.get(año='1999')
        self.assertEqual(r.context['total_proyectos'], 0)
        self.assertContains(r, 'No hay auditorías registradas')

    def test_anio_invalido_se_ignora(self):
        self.assertEqual(self.get(año='abc').context['total_proyectos'], 2)

    def test_formato_en_espanol(self):
        r = self.get()
        self.assertContains(r, ' de 20')          # "2 de noviembre de 2026"
        self.assertContains(r, 'width: 100.00%')  # el ancho CSS no usa coma decimal

    def test_no_publica_nombres_de_empresas(self):
        self.assertNotContains(self.get(), 'Empresa 1')

    def test_librerias_desde_cdn_permitido_por_csp(self):
        r = self.get()
        self.assertNotContains(r, 'unpkg.com')
        self.assertContains(r, 'cdn.jsdelivr.net/npm/leaflet@1.9.4')

    def test_coordenadas_invalidas_no_van_al_mapa(self):
        CentroPevi.objects.filter(id=self.caribe.id).update(longitud=-7310523848650743.0)
        r = self.get()
        self.assertEqual(self.datos(r)['mapa'], [])
        self.assertIn('UA', {c['sigla'] for c in r.context['centros_tabla']})
