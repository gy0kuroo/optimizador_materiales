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
