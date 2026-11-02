"""
Tests de creación de proyectos y acceso posterior al expediente.

Contexto: un PROFESOR reporta 403 después de llenar el formulario de
"Nuevo Proyecto". Estos tests recrean cada escenario posible.

Causa principal encontrada: el profesor elegía a OTRO líder; el proyecto se
creaba pero el redirect al expediente daba 403 porque un PROFESOR solo tenía
acceso si era el líder. Corregido: el PROFESOR del equipo tiene acceso y el
creador queda en el equipo automáticamente.
"""
from datetime import date
from django.test import TestCase, Client
from django.urls import reverse

from auditorias.models import Empresa, ProyectoAuditoria
from gestion.models import CentroPevi, Usuario


class BaseProyectoTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.centro_a = CentroPevi.objects.create(nombre='Centro A', codigo_interno='CA', region='Caribe')
        cls.centro_b = CentroPevi.objects.create(nombre='Centro B', codigo_interno='CB', region='Andina')

        cls.director_a = cls.crear_usuario('director_a', 'DIRECTOR_CENTRO', cls.centro_a)
        cls.profesor_a = cls.crear_usuario('profesor_a', 'PROFESOR', cls.centro_a)
        cls.profesor_a2 = cls.crear_usuario('profesor_a2', 'PROFESOR', cls.centro_a)
        cls.estudiante_a = cls.crear_usuario('estudiante_a', 'ESTUDIANTE', cls.centro_a)
        cls.profesor_b = cls.crear_usuario('profesor_b', 'PROFESOR', cls.centro_b)
        cls.profesor_sin_centro = cls.crear_usuario('profesor_sc', 'PROFESOR', None)
        cls.nacional = cls.crear_usuario('nacional', 'DIRECTOR_NACIONAL', None)

        # Empresa del centro A creada por el DIRECTOR (no por el profesor).
        # Nota: Empresa no tiene campo "creador"; solo importa el centro.
        cls.empresa_a = cls.crear_empresa('900000001', cls.centro_a)
        cls.empresa_b = cls.crear_empresa('900000002', cls.centro_b)
        cls.empresa_sin_centro = cls.crear_empresa('900000003', None)

    @staticmethod
    def crear_usuario(username, rol, centro):
        return Usuario.objects.create_user(
            username=username, password='x', email=f'{username}@test.co',
            first_name=username, rol=rol, centro_pevi=centro,
        )

    @staticmethod
    def crear_empresa(nit, centro):
        return Empresa.objects.create(
            razon_social=f'Empresa {nit}', nit=nit, centro=centro,
            sector_productivo='Alimentos', direccion='Calle 1', ciudad='Cali',
            contacto_nombre='Contacto', contacto_email='c@test.co', contacto_telefono='300',
        )

    def datos_proyecto(self, empresa, lider=None, equipo=()):
        data = {
            'nombre_proyecto': 'Auditoría Planta 1',
            'empresa': empresa.id,
            'fase': '',
            'fecha_inicio': date.today().isoformat(),
            'fecha_cierre_estimada': '',
            'lider_proyecto': lider.id if lider else '',
        }
        if equipo:
            data['equipo'] = [u.id for u in equipo]
        return data

    def login(self, user):
        client = Client()
        client.force_login(user)
        return client


class CrearProyectoProfesorTests(BaseProyectoTestCase):
    url = reverse('crear_proyecto')

    def test_profesor_puede_abrir_formulario(self):
        r = self.login(self.profesor_a).get(self.url)
        self.assertEqual(r.status_code, 200)

    def test_profesor_crea_proyecto_en_empresa_creada_por_otro(self):
        """La empresa la creó el director: el profesor igual puede usarla (mismo centro)."""
        client = self.login(self.profesor_a)
        r = client.post(self.url, self.datos_proyecto(self.empresa_a, lider=self.profesor_a))

        proyecto = ProyectoAuditoria.objects.get()
        self.assertRedirects(r, reverse('detalle_proyecto', args=[proyecto.id]))
        self.assertEqual(proyecto.centro, self.centro_a)
        self.assertEqual(proyecto.lider_proyecto, self.profesor_a)

    def test_profesor_sin_lider_es_error_de_formulario(self):
        """
        lider_proyecto es obligatorio en el form, así que la auto-asignación de
        crear_proyecto() nunca se ejecuta: el GET ya lo preselecciona y si lo
        borra, ve un error de formulario (no 403).
        """
        client = self.login(self.profesor_a)
        r = client.get(self.url)
        self.assertEqual(r.context['form'].initial.get('lider_proyecto'), self.profesor_a)

        r = client.post(self.url, self.datos_proyecto(self.empresa_a, lider=None))
        self.assertEqual(r.status_code, 200)
        self.assertIn('lider_proyecto', r.context['form'].errors)
        self.assertFalse(ProyectoAuditoria.objects.exists())

    def test_profesor_asigna_otro_lider_no_termina_en_403(self):
        """
        Caso del reporte: el profesor elige a OTRO profesor como líder. Antes el
        proyecto se creaba pero el redirect al expediente daba 403. Ahora el
        creador queda en el equipo y puede ver el proyecto.
        """
        client = self.login(self.profesor_a)
        r = client.post(self.url, self.datos_proyecto(self.empresa_a, lider=self.profesor_a2), follow=True)

        proyecto = ProyectoAuditoria.objects.get()
        self.assertEqual(r.status_code, 200)
        self.assertEqual(proyecto.lider_proyecto, self.profesor_a2)
        self.assertIn(self.profesor_a, proyecto.equipo.all())

    def test_profesor_asigna_otro_lider_y_se_incluye_en_equipo(self):
        """Si el profesor ya se había agregado al equipo, no se duplica y ve el proyecto."""
        client = self.login(self.profesor_a)
        r = client.post(
            self.url,
            self.datos_proyecto(self.empresa_a, lider=self.profesor_a2, equipo=[self.profesor_a]),
            follow=True,
        )

        proyecto = ProyectoAuditoria.objects.get()
        self.assertEqual(r.status_code, 200)
        self.assertEqual(proyecto.equipo.filter(id=self.profesor_a.id).count(), 1)

    def test_profesor_lider_no_se_agrega_al_equipo(self):
        """Si el profesor es el líder, no se agrega también al equipo."""
        self.login(self.profesor_a).post(self.url, self.datos_proyecto(self.empresa_a, lider=self.profesor_a))
        self.assertFalse(ProyectoAuditoria.objects.get().equipo.exists())

    def test_profesor_sin_centro_no_ve_formulario(self):
        """Profesor SIN centro: se le avisa antes de llenar el formulario (redirect + mensaje)."""
        client = self.login(self.profesor_sin_centro)
        r = client.get(self.url, follow=True)

        self.assertRedirects(r, reverse('lista_proyectos'))
        self.assertIn('no tiene un Centro PEVI asignado', ' '.join(str(m) for m in r.context['messages']))

    def test_profesor_sin_centro_post_no_crea_ni_da_403(self):
        """Profesor sin centro: un POST directo (cualquier empresa) redirige sin crear nada."""
        client = self.login(self.profesor_sin_centro)
        for empresa in (self.empresa_a, self.empresa_sin_centro):
            r = client.post(self.url, self.datos_proyecto(empresa, lider=self.profesor_sin_centro))
            self.assertRedirects(r, reverse('lista_proyectos'), fetch_redirect_response=False)
        self.assertFalse(ProyectoAuditoria.objects.exists())

    def test_profesor_no_puede_usar_empresa_de_otro_centro(self):
        """POST manipulado con empresa de otro centro: error de formulario, no 403."""
        client = self.login(self.profesor_a)
        r = client.post(self.url, self.datos_proyecto(self.empresa_b, lider=self.profesor_a))

        self.assertEqual(r.status_code, 200)
        self.assertIn('empresa', r.context['form'].errors)
        self.assertFalse(ProyectoAuditoria.objects.exists())

    def test_profesor_no_ve_empresa_sin_centro(self):
        """Empresas sin centro (datos legados) no aparecen ni se pueden usar."""
        client = self.login(self.profesor_a)
        r = client.get(self.url)
        self.assertNotIn(self.empresa_sin_centro, r.context['form'].fields['empresa'].queryset)

        r = client.post(self.url, self.datos_proyecto(self.empresa_sin_centro, lider=self.profesor_a))
        self.assertEqual(r.status_code, 200)
        self.assertIn('empresa', r.context['form'].errors)
        self.assertFalse(ProyectoAuditoria.objects.exists())

    def test_profesor_no_puede_asignar_lider_de_otro_centro(self):
        client = self.login(self.profesor_a)
        r = client.post(self.url, self.datos_proyecto(self.empresa_a, lider=self.profesor_b))

        self.assertEqual(r.status_code, 200)
        self.assertIn('lider_proyecto', r.context['form'].errors)
        self.assertFalse(ProyectoAuditoria.objects.exists())

    def test_profesor_no_puede_agregar_equipo_de_otro_centro(self):
        client = self.login(self.profesor_a)
        r = client.post(
            self.url,
            self.datos_proyecto(self.empresa_a, lider=self.profesor_a, equipo=[self.profesor_b]),
        )

        self.assertEqual(r.status_code, 200)
        self.assertIn('equipo', r.context['form'].errors)
        self.assertFalse(ProyectoAuditoria.objects.exists())

    def test_post_sin_csrf_da_403(self):
        """
        Sesión/pestaña vieja o cookie CSRF perdida: Django responde 403 (CSRF)
        tras llenar el formulario. Es otra causa real de "403 al guardar".
        """
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.profesor_a)
        r = client.post(self.url, self.datos_proyecto(self.empresa_a, lider=self.profesor_a))

        self.assertEqual(r.status_code, 403)
        self.assertFalse(ProyectoAuditoria.objects.exists())


class CrearProyectoOtrosRolesTests(BaseProyectoTestCase):
    url = reverse('crear_proyecto')

    def test_estudiante_no_puede_crear(self):
        self.assertEqual(self.login(self.estudiante_a).get(self.url).status_code, 403)

    def test_rol_legado_no_reconocido_da_403(self):
        """Roles viejos (p.ej. 'LIDER', 'INGENIERO') no están en los decoradores → 403."""
        legado = self.crear_usuario('legado', 'LIDER', self.centro_a)
        self.assertEqual(self.login(legado).get(self.url).status_code, 403)

    def test_director_centro_crea_y_asigna_profesor_como_lider(self):
        client = self.login(self.director_a)
        r = client.post(self.url, self.datos_proyecto(self.empresa_a, lider=self.profesor_a), follow=True)

        self.assertEqual(r.status_code, 200)
        proyecto = ProyectoAuditoria.objects.get()
        self.assertEqual(proyecto.lider_proyecto, self.profesor_a)
        # El profesor asignado como líder sí ve el proyecto
        r = self.login(self.profesor_a).get(reverse('detalle_proyecto', args=[proyecto.id]))
        self.assertEqual(r.status_code, 200)

    def test_nacional_sin_centro_hereda_centro_de_empresa(self):
        client = self.login(self.nacional)
        r = client.post(self.url, self.datos_proyecto(self.empresa_b, lider=self.profesor_b), follow=True)

        self.assertEqual(r.status_code, 200)
        self.assertEqual(ProyectoAuditoria.objects.get().centro, self.centro_b)


class AccesoProyectoTests(BaseProyectoTestCase):

    def setUp(self):
        self.proyecto = ProyectoAuditoria.objects.create(
            centro=self.centro_a, empresa=self.empresa_a, lider_proyecto=self.profesor_a,
            nombre_proyecto='P1', fecha_inicio=date.today(),
        )
        self.proyecto.equipo.add(self.estudiante_a)
        self.url = reverse('detalle_proyecto', args=[self.proyecto.id])

    def test_lider_ve_proyecto(self):
        self.assertEqual(self.login(self.profesor_a).get(self.url).status_code, 200)

    def test_estudiante_del_equipo_ve_proyecto(self):
        self.assertEqual(self.login(self.estudiante_a).get(self.url).status_code, 200)

    def test_director_del_centro_ve_proyecto(self):
        self.assertEqual(self.login(self.director_a).get(self.url).status_code, 200)

    def test_profesor_de_otro_centro_no_ve_proyecto(self):
        self.assertEqual(self.login(self.profesor_b).get(self.url).status_code, 403)

    def test_profesor_mismo_centro_no_asignado_no_ve_proyecto(self):
        self.assertEqual(self.login(self.profesor_a2).get(self.url).status_code, 403)

    def test_profesor_en_equipo_ve_proyecto(self):
        """Un PROFESOR agregado al equipo (no líder) puede ver el proyecto."""
        self.proyecto.equipo.add(self.profesor_a2)
        self.assertEqual(self.login(self.profesor_a2).get(self.url).status_code, 200)

    def test_solo_gestores_ven_botones_de_estado(self):
        """El líder y el director ven los botones de gestión; el profesor del equipo no."""
        self.proyecto.equipo.add(self.profesor_a2)
        self.assertTrue(self.login(self.profesor_a).get(self.url).context['puede_gestionar'])
        self.assertTrue(self.login(self.director_a).get(self.url).context['puede_gestionar'])
        self.assertFalse(self.login(self.profesor_a2).get(self.url).context['puede_gestionar'])


class CambiarEstadoProyectoTests(BaseProyectoTestCase):

    def setUp(self):
        self.proyecto = ProyectoAuditoria.objects.create(
            centro=self.centro_a, empresa=self.empresa_a, lider_proyecto=self.profesor_a,
            nombre_proyecto='P1', fecha_inicio=date.today(),
        )
        self.proyecto.equipo.add(self.profesor_a2)
        self.url = reverse('cambiar_estado', args=[self.proyecto.id, 'EJECUCION'])

    def test_lider_cambia_estado(self):
        self.login(self.profesor_a).get(self.url)
        self.proyecto.refresh_from_db()
        self.assertEqual(self.proyecto.estado, 'EJECUCION')

    def test_director_del_centro_cambia_estado(self):
        self.login(self.director_a).get(self.url)
        self.proyecto.refresh_from_db()
        self.assertEqual(self.proyecto.estado, 'EJECUCION')

    def test_profesor_del_equipo_no_cambia_estado(self):
        """Ser del equipo da acceso de lectura/registro, no de gestión."""
        r = self.login(self.profesor_a2).get(self.url)
        self.assertEqual(r.status_code, 403)
        self.proyecto.refresh_from_db()
        self.assertEqual(self.proyecto.estado, 'BORRADOR')

    def test_profesor_del_equipo_no_edita_proyecto(self):
        r = self.login(self.profesor_a2).get(reverse('editar_proyecto', args=[self.proyecto.id]))
        self.assertEqual(r.status_code, 403)


class CoordinadorCentroTests(BaseProyectoTestCase):
    """Coordinador de Centro: acceso total a SU centro, nada de otros centros."""

    def setUp(self):
        from gestion.models import SolicitudUsuario
        self.coord = self.crear_usuario('coord_a', 'COORDINADOR_CENTRO', self.centro_a)
        self.c = self.login(self.coord)
        # Proyecto del centro A en el que el coordinador NO es líder ni del equipo
        self.proyecto_a = ProyectoAuditoria.objects.create(
            centro=self.centro_a, empresa=self.empresa_a, lider_proyecto=self.profesor_a,
            nombre_proyecto='PA', fecha_inicio=date.today(),
        )
        self.proyecto_b = ProyectoAuditoria.objects.create(
            centro=self.centro_b, empresa=self.empresa_b, lider_proyecto=self.profesor_b,
            nombre_proyecto='PB', fecha_inicio=date.today(),
        )
        self.sol_a = SolicitudUsuario.objects.create(
            nombres='Ana', apellidos='Ruiz', email='ana@test.co',
            centro_pevi=self.centro_a, rol_solicitado='PROFESOR')
        self.sol_b = SolicitudUsuario.objects.create(
            nombres='Beto', apellidos='Paz', email='beto@test.co',
            centro_pevi=self.centro_b, rol_solicitado='ESTUDIANTE')

    # --- Proyectos y empresas de su centro ---
    def test_ve_y_gestiona_proyectos_de_su_centro(self):
        r = self.c.get(reverse('detalle_proyecto', args=[self.proyecto_a.id]))
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.context['puede_gestionar'])
        self.assertEqual(self.c.get(reverse('editar_proyecto', args=[self.proyecto_a.id])).status_code, 200)

    def test_no_ve_proyectos_de_otro_centro(self):
        self.assertEqual(self.c.get(reverse('detalle_proyecto', args=[self.proyecto_b.id])).status_code, 403)

    def test_lista_de_proyectos_solo_su_centro(self):
        ids = {p.id for p in self.c.get(reverse('lista_proyectos')).context['proyectos']}
        self.assertIn(self.proyecto_a.id, ids)
        self.assertNotIn(self.proyecto_b.id, ids)

    def test_crea_proyecto_en_su_centro(self):
        r = self.c.post(reverse('crear_proyecto'), self.datos_proyecto(self.empresa_a, lider=self.profesor_a))
        self.assertEqual(r.status_code, 302)
        self.assertTrue(ProyectoAuditoria.objects.filter(
            centro=self.centro_a, nombre_proyecto='Auditoría Planta 1').exists())

    def test_ve_empresas_metricas_y_dashboard(self):
        self.assertEqual(self.c.get(reverse('lista_empresas')).status_code, 200)
        self.assertEqual(self.c.get(reverse('dashboard_estrategico')).status_code, 200)
        self.assertEqual(self.c.get(reverse('dashboard')).status_code, 200)

    def test_sin_panel_de_control_ni_tablero_nacional(self):
        self.assertEqual(self.c.get(reverse('control_panel')).status_code, 403)
        self.assertEqual(self.c.get(reverse('dashboard_nacional')).status_code, 403)

    # --- Reabrir finalizados ---
    def test_reabre_proyecto_finalizado_de_su_centro(self):
        self.proyecto_a.estado = 'FINALIZADO'
        self.proyecto_a.save()
        self.c.get(reverse('cambiar_estado', args=[self.proyecto_a.id, 'EJECUCION']))
        self.proyecto_a.refresh_from_db()
        self.assertEqual(self.proyecto_a.estado, 'EJECUCION')

    def test_director_no_reabre_finalizado(self):
        self.proyecto_a.estado = 'FINALIZADO'
        self.proyecto_a.save()
        self.login(self.director_a).get(reverse('cambiar_estado', args=[self.proyecto_a.id, 'EJECUCION']))
        self.proyecto_a.refresh_from_db()
        self.assertEqual(self.proyecto_a.estado, 'FINALIZADO')

    # --- Usuarios ---
    def _datos_usuario(self, username, rol):
        return {'username': username, 'first_name': 'N', 'last_name': 'A', 'email': f'{username}@t.co',
                'rol': rol, 'cargo': '', 'password1': 'ClaveSegura#2026', 'password2': 'ClaveSegura#2026'}

    def test_crea_director_en_su_centro(self):
        self.c.post(reverse('crear_usuario'), self._datos_usuario('nuevo_dir', 'DIRECTOR_CENTRO'))
        u = Usuario.objects.get(username='nuevo_dir')
        self.assertEqual((u.rol, u.centro_pevi, u.is_superuser), ('DIRECTOR_CENTRO', self.centro_a, False))

    def test_no_crea_roles_superiores(self):
        for rol in ('DIRECTOR_NACIONAL', 'COORDINADOR', 'COORDINADOR_CENTRO'):
            username = 'x_' + rol.lower()
            self.c.post(reverse('crear_usuario'), self._datos_usuario(username, rol))
            self.assertFalse(Usuario.objects.filter(username=username).exists(), rol)

    def test_director_no_crea_directores(self):
        self.login(self.director_a).post(reverse('crear_usuario'), self._datos_usuario('dir2', 'DIRECTOR_CENTRO'))
        self.assertFalse(Usuario.objects.filter(username='dir2').exists())

    def test_edita_director_de_su_centro_pero_no_de_otro(self):
        director_b = self.crear_usuario('director_b', 'DIRECTOR_CENTRO', self.centro_b)
        self.assertEqual(self.c.get(reverse('editar_usuario', args=[self.director_a.id])).status_code, 200)
        self.assertEqual(self.c.get(reverse('editar_usuario', args=[director_b.id])).status_code, 403)

    def test_no_edita_ni_elimina_nacional(self):
        self.assertEqual(self.c.get(reverse('editar_usuario', args=[self.nacional.id])).status_code, 403)
        self.assertEqual(self.c.get(reverse('eliminar_usuario', args=[self.nacional.id])).status_code, 403)
        self.assertTrue(Usuario.objects.filter(id=self.nacional.id).exists())

    def test_director_no_elimina_coordinador(self):
        r = self.login(self.director_a).get(reverse('eliminar_usuario', args=[self.coord.id]))
        self.assertEqual(r.status_code, 403)
        self.assertTrue(Usuario.objects.filter(id=self.coord.id).exists())

    # --- Solicitudes de acceso ---
    def test_lista_solo_solicitudes_de_su_centro(self):
        r = self.c.get(reverse('solicitudes_centro'))
        self.assertEqual({s.id for s in r.context['solicitudes']}, {self.sol_a.id})

    def test_director_no_ve_solicitudes(self):
        self.assertEqual(self.login(self.director_a).get(reverse('solicitudes_centro')).status_code, 403)

    def test_aprobar_solicitud_crea_usuario_y_la_marca(self):
        r = self.c.get(reverse('crear_usuario') + f'?solicitud={self.sol_a.id}')
        self.assertEqual(r.context['form'].initial['email'], 'ana@test.co')
        datos = self._datos_usuario('ana', 'PROFESOR')
        datos['solicitud_id'] = self.sol_a.id
        self.c.post(reverse('crear_usuario'), datos)
        self.sol_a.refresh_from_db()
        self.assertEqual(self.sol_a.estado, 'APROBADA')
        self.assertEqual(self.sol_a.usuario_creado.username, 'ana')
        self.assertEqual(self.sol_a.usuario_creado.centro_pevi, self.centro_a)

    def test_no_aprueba_solicitud_de_otro_centro(self):
        datos = self._datos_usuario('beto', 'ESTUDIANTE')
        datos['solicitud_id'] = self.sol_b.id
        self.c.post(reverse('crear_usuario'), datos)
        self.sol_b.refresh_from_db()
        self.assertEqual(self.sol_b.estado, 'PENDIENTE')

    def test_rechaza_solo_de_su_centro(self):
        self.c.post(reverse('rechazar_solicitud_centro', args=[self.sol_a.id]))
        r = self.c.post(reverse('rechazar_solicitud_centro', args=[self.sol_b.id]))
        self.sol_a.refresh_from_db()
        self.sol_b.refresh_from_db()
        self.assertEqual((self.sol_a.estado, self.sol_b.estado), ('RECHAZADA', 'PENDIENTE'))
        self.assertEqual(r.status_code, 404)
