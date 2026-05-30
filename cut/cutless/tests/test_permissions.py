from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class PermisosVistaTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user('operario', password='test12345')
        self.perfil = self.usuario.perfil
        self.perfil.puede_ver_estadisticas = False
        self.perfil.puede_crear_materiales = False
        self.perfil.puede_comparar_optimizaciones = False
        self.perfil.puede_crear_presupuestos = False
        self.perfil.puede_ver_historial_costos = False
        self.perfil.save()

    def test_estadisticas_bloqueada_sin_permiso(self):
        self.client.login(username='operario', password='test12345')
        response = self.client.get(reverse('cutless:estadisticas'))
        self.assertRedirects(response, reverse('cutless:index'))

    def test_estadisticas_accesible_con_permiso(self):
        self.perfil.puede_ver_estadisticas = True
        self.perfil.save()
        self.client.login(username='operario', password='test12345')
        response = self.client.get(reverse('cutless:estadisticas'))
        self.assertEqual(response.status_code, 200)

    def test_materiales_bloqueado_sin_permiso(self):
        self.client.login(username='operario', password='test12345')
        response = self.client.get(reverse('cutless:lista_materiales'))
        self.assertRedirects(response, reverse('cutless:index'))

    def test_comparar_bloqueada_sin_permiso(self):
        self.client.login(username='operario', password='test12345')
        response = self.client.get(reverse('cutless:comparar_optimizaciones'))
        self.assertRedirects(response, reverse('cutless:index'))

    def test_admin_rol_accede_sin_flag_explicito(self):
        self.perfil.rol = 'admin'
        self.perfil.save()
        self.client.login(username='operario', password='test12345')
        response = self.client.get(reverse('cutless:estadisticas'))
        self.assertEqual(response.status_code, 200)

    def test_index_siempre_accesible_autenticado(self):
        self.client.login(username='operario', password='test12345')
        response = self.client.get(reverse('cutless:index'))
        self.assertEqual(response.status_code, 200)

    def test_presupuestos_bloqueados_sin_permiso(self):
        self.client.login(username='operario', password='test12345')
        response = self.client.get(reverse('cutless:lista_presupuestos'))
        self.assertRedirects(response, reverse('cutless:index'))

    def test_historial_costos_bloqueado_sin_permiso(self):
        self.client.login(username='operario', password='test12345')
        response = self.client.get(reverse('cutless:historial_costos'))
        self.assertRedirects(response, reverse('cutless:index'))

    def test_export_estadisticas_bloqueada_sin_permiso(self):
        self.client.login(username='operario', password='test12345')
        response = self.client.get(reverse('cutless:exportar_excel_desperdicio'))
        self.assertRedirects(response, reverse('cutless:index'))
