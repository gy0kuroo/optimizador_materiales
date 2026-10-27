from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from .forms import AccesoForm, RegistroForm


class AuthFeedbackTests(TestCase):
    def data(self, **changes):
        data = {'username':'persona_nueva', 'email':'persona@example.com',
                'password1':'Madera!Temporal9274', 'password2':'Madera!Temporal9274'}
        data.update(changes)
        return data

    def test_registro_invalido_conserva_datos_y_explicacion_accesible(self):
        response = self.client.post(reverse('usuarios:registro'), self.data(email='mal', password2='Otra'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Escribe un correo válido')
        self.assertContains(response, 'Las contraseñas no coinciden')
        self.assertContains(response, 'value="persona_nueva"')
        self.assertNotContains(response, 'value="Madera!Temporal9274"')
        self.assertContains(response, 'aria-invalid="true"')
        self.assertContains(response, 'id="id_email_errors"')
        self.assertFalse(User.objects.filter(username='persona_nueva').exists())

    def test_validadores_de_contrasena_siguen_activos(self):
        form = RegistroForm(self.data(password1='123', password2='123'))
        self.assertFalse(form.is_valid())
        self.assertIn('password_too_short', [e.code for e in form.errors.as_data()['password2']])
        self.assertIn('Usa al menos 8 caracteres.', form.errors['password2'])
        self.assertIn('Esta contraseña es muy común.', str(form.errors))

    def test_usuario_repetido_recibe_mensaje_concreto(self):
        User.objects.create_user('persona_nueva')
        form = RegistroForm(self.data())
        self.assertFalse(form.is_valid())
        self.assertIn('Este nombre de usuario ya está en uso. Prueba con otro.', form.errors['username'])

    def test_cuenta_creada_muestra_una_sola_confirmacion_en_panel_login(self):
        response = self.client.post(reverse('usuarios:registro'), self.data(), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Tu cuenta está lista. Ahora inicia sesión.', count=1)
        self.assertContains(response, 'auth-notice')
        self.assertFalse('_auth_user_id' in self.client.session)
        user = User.objects.get(username='persona_nueva')
        self.assertTrue(user.check_password(self.data()['password1']))

    def test_login_no_revela_si_el_usuario_existe(self):
        User.objects.create_user('existente', password='Madera!Temporal9274')
        errors = []
        for username in ['existente', 'desconocido']:
            form = AccesoForm(data={'username':username, 'password':'incorrecta'})
            self.assertFalse(form.is_valid())
            errors.append(list(form.non_field_errors()))
        self.assertEqual(errors[0], errors[1])
        self.assertIn('No pudimos iniciar sesión.', errors[0][0])

    @override_settings(AUTH_PASSWORD_VALIDATORS=[{
        'NAME':'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS':{'min_length':12},
    }])
    def test_guia_utiliza_la_longitud_configurada_en_servidor(self):
        self.assertEqual(RegistroForm().password_min_length, 12)
        response = self.client.get(reverse('usuarios:registro'))
        self.assertContains(response, 'data-min-password="12"')
        self.assertContains(response, 'Al menos 12 caracteres.')
        self.assertNotContains(response, 'data-password-rule="numeric"')
