import re
from django.contrib.auth.models import User
from django.test import Client, TestCase, override_settings
from django.urls import reverse


class CsrfRecoveryTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('csrf_revision', password='RevisionTemporal123')
        self.client = Client(enforce_csrf_checks=True)
        self.url = reverse('usuarios:login')

    def formulario(self):
        response = self.client.get(self.url)
        token = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', response.content.decode())[1]
        return response, token

    def test_login_y_registro_no_se_guardan_en_cache(self):
        for url in (self.url, reverse('usuarios:registro')):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertIn('no-store', response['Cache-Control'])
            self.assertContains(response, 'auth-history.js')

    @override_settings(DEBUG=True)
    def test_reenvio_login_antiguo_es_rechazado_con_pantalla_clara(self):
        _, old_token = self.formulario()
        data = {'username': 'csrf_revision', 'password': 'RevisionTemporal123', 'csrfmiddlewaretoken': old_token}
        self.assertEqual(self.client.post(self.url, data).status_code, 302)
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, 'usuarios/formulario_desactualizado.html')
        self.assertContains(response, 'Este envío no se procesó.', status_code=403)
        self.assertContains(response, 'Continuar en Inicio', status_code=403)
        self.assertNotContains(response, 'Reason given for failure', status_code=403)
        self.assertNotContains(response, 'RevisionTemporal123', status_code=403)
        self.assertEqual(self.client.session['_auth_user_id'], str(self.user.pk))
        self.assertIn('no-store', response['Cache-Control'])

    def test_solicitud_sin_token_no_inicia_sesion(self):
        response = self.client.post(self.url, {'username': 'csrf_revision', 'password': 'RevisionTemporal123'})
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, 'Volver a iniciar sesión', status_code=403)
        self.assertNotIn('_auth_user_id', self.client.session)
        # La recuperación es GET: proporciona un token nuevo sin repetir el POST.
        form, token = self.formulario()
        self.assertEqual(self.client.post(self.url, {'username': 'csrf_revision',
            'password': 'RevisionTemporal123', 'csrfmiddlewaretoken': token}).status_code, 302)

    def test_credenciales_incorrectas_con_token_valido_conservan_error_habitual(self):
        _, token = self.formulario()
        response = self.client.post(self.url, {'username': 'csrf_revision',
            'password': 'incorrecta', 'csrfmiddlewaretoken': token})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'usuarios/login.html')
        self.assertTrue(response.context['form'].errors)

    def test_csrf_ajax_devuelve_json_403_sin_detalles_internos(self):
        response = self.client.post(self.url, {}, HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()['error'], 'formulario_desactualizado')
        self.assertEqual(response.json()['recovery_url'], self.url)

    def test_login_autenticado_obtiene_redireccion_sin_formulario_antiguo(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('no-store', response['Cache-Control'])
