"""La página final debe ser un GET seguro para recargar, sin repetir el POST."""
from unittest.mock import patch
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from cutless.models import Optimizacion

class ResultadoRecargaTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('resultado_recarga')
        self.user.perfil.rol = 'usuario'
        self.user.perfil.preferencias_menu = {'_inicio_completado': True}
        self.user.perfil.save()
        self.client.force_login(self.user)
        self.data = {'unidad_medida':'cm', 'ancho':122, 'alto':244, 'margen_corte':3,
            'permitir_rotacion':'on', 'form-TOTAL_FORMS':1, 'form-INITIAL_FORMS':0,
            'form-0-nombre':'Puerta', 'form-0-ancho':40, 'form-0-alto':50, 'form-0-cantidad':2}

    def test_create_redirects_and_refreshes_never_create_or_recalculate(self):
        response = self.client.post(reverse('cutless:index'), self.data)
        opt = Optimizacion.objects.get(usuario=self.user)
        url = reverse('cutless:resultado', args=[opt.pk])
        self.assertRedirects(response, url, fetch_redirect_response=False)
        before = Optimizacion.objects.values().get(pk=opt.pk)
        with patch('cutless.services.optimization._regenerar_grafico', side_effect=AssertionError('No recalcular')):
            with patch('cutless.exports.board_png.generar_png_tablero', side_effect=AssertionError('El SVG no necesita PNG')):
                for _ in range(3):
                    result = self.client.get(url, HTTP_CACHE_CONTROL='no-cache', HTTP_PRAGMA='no-cache')
                    self.assertEqual(result.status_code, 200)
                    self.assertTemplateUsed(result, 'cutless/resultado.html')
        self.assertEqual(Optimizacion.objects.filter(usuario=self.user).count(), 1)
        self.assertEqual(Optimizacion.objects.values().get(pk=opt.pk), before)

    def test_edit_redirects_to_same_record_and_invalid_submission_stays_on_form(self):
        self.client.post(reverse('cutless:index'), self.data)
        opt = Optimizacion.objects.get(usuario=self.user)
        url = reverse('cutless:editar_optimizacion', args=[opt.pk])
        response = self.client.post(url, {**self.data, 'form-0-cantidad':3})
        self.assertRedirects(response, reverse('cutless:resultado', args=[opt.pk]), fetch_redirect_response=False)
        self.assertEqual(Optimizacion.objects.filter(usuario=self.user).count(), 1)
        opt.refresh_from_db()
        self.assertIn(',3', opt.piezas)
        invalid = self.client.post(url, {**self.data, 'ancho':99999})
        self.assertEqual(invalid.status_code, 200)
        self.assertTemplateUsed(invalid, 'cutless/editar_optimizacion.html')
        self.assertEqual(Optimizacion.objects.filter(usuario=self.user).count(), 1)

    def test_another_user_cannot_read_result(self):
        self.client.post(reverse('cutless:index'), self.data)
        opt = Optimizacion.objects.get(usuario=self.user)
        other = User.objects.create_user('otro_resultado')
        self.client.force_login(other)
        self.assertEqual(self.client.get(reverse('cutless:resultado', args=[opt.pk])).status_code, 404)
