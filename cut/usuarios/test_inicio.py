from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from usuarios.forms import ConfiguracionInicialForm


class ConfiguracionInicialTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user('inicio', password='prueba-segura-123')
        self.perfil = self.usuario.perfil
        self.url = reverse('usuarios:configuracion_inicial')
        self.datos = {'modo': 'esencial', 'tema_preferido': 'auto', 'tamanio_fuente': 'large'}

    def test_primer_login_abre_configuracion_y_despues_no_se_repite(self):
        login = reverse('usuarios:login')
        credenciales = {'username': 'inicio', 'password': 'prueba-segura-123'}
        self.assertRedirects(self.client.post(login, credenciales), self.url)
        self.assertRedirects(self.client.post(self.url, self.datos), reverse('cutless:index'))
        self.client.logout()
        self.assertRedirects(self.client.post(login, credenciales), reverse('cutless:index'))

    def test_esencial_guarda_apariencia_sin_tocar_permisos_ni_tutorial(self):
        self.client.force_login(self.usuario)
        self.perfil.timeout_sesion = 75
        self.perfil.preferencias_menu = {'otro_ajuste': 'conservar'}
        self.perfil.save()
        self.client.post(self.url, {**self.datos, 'materiales': 'on', 'puede_crear_clientes': ''})
        self.perfil.refresh_from_db()
        self.assertTrue(self.perfil.inicio_personalizado)
        self.assertTrue(self.perfil.puede_crear_clientes)
        self.assertFalse(self.perfil.tutorial_completado)
        self.assertEqual(self.perfil.timeout_sesion, 75)
        self.assertEqual(self.perfil.tamanio_fuente, 'large')
        self.assertEqual(self.perfil.preferencias_menu['otro_ajuste'], 'conservar')
        self.assertFalse(self.perfil.menu_visible['gestion'])
        self.assertFalse(self.perfil.menu_visible['analisis'])
        response = self.client.get(reverse('cutless:index'))
        self.assertContains(response, 'Historial')
        self.assertNotContains(response, 'id="nav-gestion"')

    def test_personalizado_solo_guarda_herramientas_autorizadas(self):
        self.client.force_login(self.usuario)
        self.perfil.puede_ver_estadisticas = False
        self.perfil.save()
        self.client.post(self.url, {**self.datos, 'modo': 'personalizado',
                                   'clientes': 'on', 'estadisticas': 'on'})
        self.perfil.refresh_from_db()
        self.assertTrue(self.perfil.menu_visible['clientes'])
        self.assertFalse(self.perfil.menu_visible['materiales'])
        self.assertFalse(self.perfil.puede_ver_estadisticas)
        self.assertFalse(self.perfil.menu_visible['estadisticas'])
        self.assertNotIn('estadisticas', self.perfil.preferencias_menu)
        form = ConfiguracionInicialForm(instance=self.perfil)
        self.assertEqual(form['modo'].value(), 'personalizado')
        self.assertTrue(form['clientes'].value())

    def test_error_no_guarda_ni_marca_completado(self):
        self.client.force_login(self.usuario)
        response = self.client.post(self.url, {**self.datos, 'tema_preferido': 'invalido'})
        self.assertEqual(response.status_code, 200)
        self.perfil.refresh_from_db()
        self.assertFalse(self.perfil.inicio_personalizado)
        self.assertEqual(self.perfil.tamanio_fuente, 'normal')
        self.assertEqual(self.perfil.preferencias_menu, {})

    def test_get_no_modifica_y_se_puede_volver_desde_cuenta(self):
        self.client.force_login(self.usuario)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Prepara CutLess para ti')
        self.assertNotContains(response, 'id="modalBienvenida"')
        self.perfil.refresh_from_db()
        self.assertFalse(self.perfil.inicio_personalizado)
        self.client.post(self.url, self.datos)
        self.assertContains(self.client.get(reverse('cutless:index')), 'Personalizar mi inicio')
        self.assertContains(self.client.get(self.url), 'Guardar mis preferencias')

    def test_sin_login_o_sin_csrf_no_guarda(self):
        self.assertEqual(self.client.get(self.url).status_code, 302)
        cliente = Client(enforce_csrf_checks=True)
        cliente.force_login(self.usuario)
        self.assertEqual(cliente.post(self.url, self.datos).status_code, 403)

