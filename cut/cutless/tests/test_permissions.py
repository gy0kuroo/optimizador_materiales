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


class MaterialesCompartidosTests(TestCase):
    def setUp(self):
        from cutless.models import Material
        self.usuario = User.objects.create_user('material_user')
        self.otro = User.objects.create_user('material_other')
        self.material = Material.objects.create(nombre='Sistema', ancho=122, alto=244, es_predefinido=True)
        self.propio = Material.objects.create(nombre='Personal', ancho=122, alto=244, usuario=self.usuario)
        self.ajeno = Material.objects.create(nombre='Ajeno', ancho=122, alto=244, usuario=self.otro)
        self.client.force_login(self.usuario)
        self.data = {'nombre': 'Modificado', 'ancho': 122, 'alto': 244, 'unidad_medida': 'cm'}

    def test_usuario_no_puede_editar_material_compartido(self):
        url = reverse('cutless:editar_material', args=[self.material.pk])
        self.assertEqual(self.client.get(url).status_code, 403)
        self.assertEqual(self.client.post(url, self.data).status_code, 403)
        self.material.refresh_from_db()
        self.assertEqual(self.material.nombre, 'Sistema')
        self.assertNotContains(self.client.get(reverse('cutless:lista_materiales')), url)

    def test_usuario_no_puede_eliminar_material_compartido(self):
        response = self.client.post(reverse('cutless:eliminar_material', args=[self.material.pk]))
        self.assertEqual(response.status_code, 403)
        self.material.refresh_from_db()

    def test_admin_y_superusuario_pueden_editar_compartidos(self):
        for superuser in (False, True):
            with self.subTest(superuser=superuser):
                self.usuario.is_superuser = superuser
                self.usuario.save()
                self.usuario.perfil.rol = 'usuario' if superuser else 'admin'
                self.usuario.perfil.save()
                response = self.client.post(reverse('cutless:editar_material', args=[self.material.pk]), self.data)
                self.assertEqual(response.status_code, 302)
                self.material.refresh_from_db()
                self.assertEqual(self.material.nombre, 'Modificado')
                self.assertIsNone(self.material.usuario_id)

    def test_usuario_puede_editar_y_eliminar_material_propio(self):
        self.assertEqual(self.client.post(reverse('cutless:editar_material', args=[self.propio.pk]), self.data).status_code, 302)
        self.propio.refresh_from_db()
        self.assertEqual(self.propio.nombre, 'Modificado')
        self.assertEqual(self.client.post(reverse('cutless:eliminar_material', args=[self.propio.pk])).status_code, 302)
        from cutless.models import Material
        self.assertFalse(Material.objects.filter(pk=self.propio.pk).exists())

    def test_material_ajeno_no_se_modifica(self):
        self.client.post(reverse('cutless:editar_material', args=[self.ajeno.pk]), self.data)
        self.ajeno.refresh_from_db()
        self.assertEqual(self.ajeno.nombre, 'Ajeno')
        self.assertEqual(self.client.post(reverse('cutless:eliminar_material', args=[self.ajeno.pk])).status_code, 404)
