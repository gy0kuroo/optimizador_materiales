from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse


class PerfilSeparadoTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user('persona', email='persona@example.com')
        self.client.force_login(self.usuario)
        self.url = reverse('usuarios:perfil')

    def test_preferencias_conservan_cuenta_y_otros_ajustes(self):
        perfil = self.usuario.perfil
        perfil.notificaciones_email = True
        perfil.unidad_medida_predeterminada = 'm'
        perfil.save()
        response = self.client.post(self.url, {'editar_perfil': '1', 'timeout_sesion': '60', 'tema_preferido': 'dark', 'tamanio_fuente': 'large'})
        self.assertEqual(response.status_code, 302)
        self.usuario.refresh_from_db()
        perfil.refresh_from_db()
        self.assertEqual(self.usuario.username, 'persona')
        self.assertEqual(self.usuario.email, 'persona@example.com')
        self.assertEqual(perfil.tamanio_fuente, 'large')
        self.assertEqual(perfil.timeout_sesion, 60)
        self.assertEqual(perfil.unidad_medida_predeterminada, 'm')
        self.assertTrue(perfil.notificaciones_email)

    def test_cuenta_conserva_preferencias(self):
        perfil = self.usuario.perfil
        perfil.timeout_sesion = 60
        perfil.tamanio_fuente = 'xlarge'
        perfil.save()
        response = self.client.post(self.url, {'editar_cuenta': '1', 'username': 'personanueva', 'email': 'nuevo@example.com'})
        self.assertEqual(response.status_code, 302)
        perfil.refresh_from_db()
        self.assertEqual(perfil.timeout_sesion, 60)
        self.assertEqual(perfil.tamanio_fuente, 'xlarge')

    def test_preferencias_invalidas_conservan_campos_cuenta(self):
        response = self.client.post(self.url, {'editar_perfil': '1', 'tema_preferido': 'dark', 'tamanio_fuente': 'invalido'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'value="persona"')
        self.assertContains(response, 'value="persona@example.com"')
        self.assertFalse(response.context['cuenta_form'].is_bound)

    def test_usuario_con_simbolos_o_carga_sql_no_se_guarda(self):
        for value in ["''", '\"\"', '@', "' OR 1=1 --", '<script>alert(1)</script>']:
            with self.subTest(value=value):
                response = self.client.post(self.url, {'editar_cuenta': '1', 'username': value, 'email': 'persona@example.com'})
                self.assertEqual(response.status_code, 200)
                self.assertIn('username', response.context['cuenta_form'].errors)
                self.usuario.refresh_from_db()
                self.assertEqual(self.usuario.username, 'persona')
                self.assertEqual(User.objects.count(), 1)
                self.assertNotContains(response, '<script>alert(1)</script>')

    def test_correo_invalido_no_se_guarda_y_arroba_valida_si(self):
        response = self.client.post(self.url, {'editar_cuenta': '1', 'username': 'persona', 'email': "' OR 1=1 --"})
        self.assertEqual(response.status_code, 200)
        self.assertIn('email', response.context['cuenta_form'].errors)
        response = self.client.post(self.url, {'editar_cuenta': '1', 'username': 'persona', 'email': 'nuevo@example.com'})
        self.assertEqual(response.status_code, 302)
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.email, 'nuevo@example.com')


class ConfiguracionSistemaTests(TestCase):
    def test_margen_no_numerico_o_no_finito_devuelve_error(self):
        user = User.objects.create_user('margenrevision')
        self.client.force_login(user)
        original = user.perfil.margen_corte_predeterminado
        for value in ['abc', 'NaN', 'Infinity', '-Infinity']:
            with self.subTest(value=value):
                response = self.client.post(reverse('usuarios:configuracion_sistema'), {
                    'editar_configuracion': '1', 'unidad_medida_predeterminada': 'cm',
                    'margen_corte_predeterminado': value,
                })
                self.assertEqual(response.status_code, 200)
                self.assertIn('margen_corte_predeterminado', response.context['perfil_form'].errors)
                user.perfil.refresh_from_db()
                self.assertEqual(user.perfil.margen_corte_predeterminado, original)

    def test_ajustes_no_modifican_cuenta_o_lectura(self):
        user = User.objects.create_user('usuario_legacy', email='')
        perfil = user.perfil
        perfil.tamanio_fuente = 'large'
        perfil.timeout_sesion = 60
        perfil.save()
        self.client.force_login(user)
        response = self.client.post(reverse('usuarios:configuracion_sistema'), {
            'editar_configuracion': '1', 'unidad_medida_predeterminada': 'm',
            'margen_corte_predeterminado': '0', 'email_notificaciones': '',
            'username': 'intruso', 'tema_preferido': 'dark',
        })
        self.assertEqual(response.status_code, 302)
        user.refresh_from_db()
        perfil.refresh_from_db()
        self.assertEqual(user.username, 'usuario_legacy')
        self.assertEqual(user.email, '')
        self.assertEqual(perfil.tamanio_fuente, 'large')
        self.assertEqual(perfil.timeout_sesion, 60)
        self.assertEqual(perfil.tema_preferido, 'auto')
        self.assertEqual(perfil.unidad_medida_predeterminada, 'm')
        self.assertEqual(perfil.margen_corte_predeterminado, 0)
        self.assertFalse(perfil.rotacion_automatica_predeterminada)

    def test_configuracion_muestra_botones_y_error_de_margen(self):
        user = User.objects.create_user('ajustes')
        self.client.force_login(user)
        url = reverse('usuarios:configuracion_sistema')
        response = self.client.get(url)
        self.assertContains(response, 'Guardar ajustes de corte y avisos')
        self.assertContains(response, 'Guardar menú')
        response = self.client.post(url, {'editar_configuracion': '1', 'unidad_medida_predeterminada': 'cm', 'margen_corte_predeterminado': '11'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('margen_corte_predeterminado', response.context['perfil_form'].errors)


class PersonalizarMenuTests(TestCase):
    def test_ocultar_no_quita_acceso_ni_modifica_permisos(self):
        user = User.objects.create_user('menu')
        self.client.force_login(user)
        response = self.client.post(reverse('usuarios:configuracion_sistema'), {'editar_permisos_menu': '1'})
        self.assertEqual(response.status_code, 302)
        user.perfil.refresh_from_db()
        self.assertTrue(user.perfil.puede_crear_materiales)
        self.assertFalse(user.perfil.menu_visible['gestion'])
        self.assertEqual(self.client.get(reverse('cutless:lista_materiales')).status_code, 200)
        response = self.client.get(reverse('cutless:index'))
        self.assertNotContains(response, 'id="nav-gestion"')
        self.client.post(reverse('usuarios:configuracion_sistema'), {'editar_permisos_menu': '1', 'materiales': 'on'})
        self.assertContains(self.client.get(reverse('cutless:index')), 'id="nav-gestion"')

    def test_personalizar_no_otorga_permiso_restringido(self):
        user = User.objects.create_user('menurestringido')
        user.perfil.puede_ver_estadisticas = False
        user.perfil.save()
        self.client.force_login(user)
        self.client.post(reverse('usuarios:configuracion_sistema'), {'editar_permisos_menu': '1', 'estadisticas': 'on', 'puede_ver_estadisticas': 'on'})
        user.perfil.refresh_from_db()
        self.assertFalse(user.perfil.puede_ver_estadisticas)
        self.assertFalse(user.perfil.menu_visible['estadisticas'])
        self.assertRedirects(self.client.get(reverse('cutless:estadisticas')), reverse('cutless:index'))


class AdminDashboardBusquedaTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user('admin_busqueda')
        self.admin.perfil.rol = 'admin'
        self.admin.perfil.save()
        self.usuario_a = User.objects.create_user('maria_soto', email='maria@example.com')
        self.usuario_b = User.objects.create_user('lucas_rojas', email='lucas@example.com')
        self.client.force_login(self.admin)

    def test_dashboard_filtra_por_username_y_email(self):
        response = self.client.get(reverse('usuarios:admin_dashboard'), {'busqueda': 'maria'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'maria_soto')
        self.assertContains(response, 'maria@example.com')
        self.assertNotContains(response, 'lucas_rojas')


class AdminDashboardPaginacionTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user('admin_paginacion')
        self.admin.perfil.rol = 'admin'
        self.admin.perfil.save()
        for numero in range(11):
            User.objects.create_user(f'usuario_paginado_{numero:02d}')
        self.client.force_login(self.admin)

    def test_dashboard_muestra_diez_usuarios_y_pagina_siguiente(self):
        response = self.client.get(reverse('usuarios:admin_dashboard'))

        self.assertEqual(len(response.context['usuarios']), 10)
        self.assertTrue(response.context['is_paginated'])
        self.assertContains(response, 'aria-label="Paginación de usuarios"')

    def test_paginacion_conserva_el_filtro_de_busqueda(self):
        response = self.client.get(
            reverse('usuarios:admin_dashboard'),
            {'busqueda': 'usuario_paginado', 'page': 2},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['usuarios']), 1)
        self.assertContains(response, 'usuario_paginado_10')
        self.assertContains(response, 'busqueda=usuario_paginado')


class AdminDashboardPresentacionTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user('admin_presentacion')
        self.admin.perfil.rol = 'admin'
        self.admin.perfil.save()
        User.objects.create_user('carpintero')
        self.client.force_login(self.admin)

    def test_tabla_agrupa_identidad_y_etiqueta_acciones_por_usuario(self):
        response = self.client.get(reverse('usuarios:admin_dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<th scope="col">Estado</th>', html=True)
        self.assertContains(response, 'aria-label="Eliminar a carpintero"')
        self.assertContains(response, 'aria-label="Rol de carpintero"')
        self.assertContains(response, 'Sin email')
        self.assertContains(response, 'Tu cuenta')
        self.assertContains(response, 'Sin acciones')
        self.assertNotContains(response, '<th scope="col">Email</th>', html=True)

    def test_creacion_conserva_ayudas_y_reglas_dinamicas_del_formulario(self):
        response = self.client.get(reverse('usuarios:admin_dashboard'))

        self.assertContains(response, 'id="id_username"')
        self.assertContains(response, 'id="id_email"')
        self.assertContains(response, 'id="id_password1"')
        self.assertContains(response, 'id="id_password2"')
        self.assertContains(response, 'class="admin-password-rules"')
        self.assertContains(response, 'admin-create-role')


class PasswordVisibilityAssetTests(TestCase):
    def test_control_de_visibilidad_se_carga_en_formularios_de_acceso(self):
        for route in ('usuarios:login', 'usuarios:registro'):
            with self.subTest(route=route):
                response = self.client.get(reverse(route))
                self.assertContains(response, 'cutless/js/password-visibility.js')


class EliminarUsuarioTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user('admin_test')
        self.admin.perfil.rol = 'admin'
        self.admin.perfil.save()
        self.usuario = User.objects.create_user('victima')
        self.url = reverse('usuarios:eliminar_usuario', args=[self.usuario.pk])
        self.client.force_login(self.admin)

    def test_get_no_elimina_usuario(self):
        self.assertEqual(self.client.get(self.url).status_code, 405)
        self.assertTrue(User.objects.filter(pk=self.usuario.pk).exists())

    def test_admin_puede_eliminar_por_post(self):
        self.assertEqual(self.client.post(self.url).status_code, 302)
        self.assertFalse(User.objects.filter(pk=self.usuario.pk).exists())

    def test_usuario_normal_no_puede_eliminar(self):
        self.client.force_login(self.usuario)
        self.client.post(self.url)
        self.assertTrue(User.objects.filter(pk=self.usuario.pk).exists())

    def test_admin_no_puede_eliminarse(self):
        self.client.post(reverse('usuarios:eliminar_usuario', args=[self.admin.pk]))
        self.assertTrue(User.objects.filter(pk=self.admin.pk).exists())

    def test_post_sin_csrf_no_elimina(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.admin)
        self.assertEqual(client.post(self.url).status_code, 403)
        self.assertTrue(User.objects.filter(pk=self.usuario.pk).exists())
