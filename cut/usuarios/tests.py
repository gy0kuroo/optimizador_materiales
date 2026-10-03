from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse


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
