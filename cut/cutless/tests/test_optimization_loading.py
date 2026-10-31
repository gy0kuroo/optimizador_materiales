from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from cutless.models import Optimizacion


class OptimizationLoadingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('espera_optimizacion')
        self.user.perfil.preferencias_menu = {'_inicio_completado': True}
        self.user.perfil.save()
        self.client.force_login(self.user)

    def test_create_uses_optimization_skeleton_and_keeps_download_spinner(self):
        response = self.client.get(reverse('cutless:index'))
        self.assertContains(response, 'data-loading-optimization')
        self.assertContains(response, 'cutless-optimization-loading-template')
        self.assertContains(response, 'optimization-loading.js')
        self.assertContains(response, 'cutless-loading-template')
        self.assertNotContains(response, 'onsubmit="mostrarIndicadorCarga')

    def test_edit_uses_same_loading_contract(self):
        opt = Optimizacion.objects.create(usuario=self.user, ancho_tablero=122, alto_tablero=244, piezas='P,25,25,5')
        response = self.client.get(reverse('cutless:editar_optimizacion', args=[opt.pk]))
        self.assertContains(response, 'data-loading-optimization')
        self.assertContains(response, 'cutless-optimization-loading-template')
        self.assertContains(response, 'optimization-loading.css')
