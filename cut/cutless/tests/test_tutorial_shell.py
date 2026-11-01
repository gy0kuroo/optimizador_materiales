"""La separación de la plantilla no debe filtrar ayuda privada ni desactivar la ayuda manual."""
from types import SimpleNamespace
from django.template import Context, Engine
from django.test import SimpleTestCase

class TutorialShellTests(SimpleTestCase):
    def render_shell(self, authenticated=True, completed=False, hidden=False):
        profile = SimpleNamespace(tutorial_completado=completed, tema_preferido='dark',
            tamanio_fuente='normal', menu_visible={}, get_timeout_segundos_str='1800')
        user = SimpleNamespace(is_authenticated=authenticated, username='revision_tutorial', perfil=profile)
        return Engine.get_default().get_template('cutless/base.html').render(Context({
            'user': user, 'ocultar_tutorial': hidden, 'csrf_token': 'revision',
            'mostrar_modal_bienvenida': True, 'tiene_optimizaciones': False}))

    def test_anonymous_and_hidden_tutorial_do_not_render_help_or_welcome(self):
        for options in [{'authenticated':False}, {'hidden':True}]:
            with self.subTest(options=options):
                html = self.render_shell(**options)
                self.assertNotIn('function iniciarTutorial()', html)
                self.assertNotIn('id="modalBienvenida"', html)

    def test_new_user_has_one_help_controller_and_one_welcome_dialog(self):
        html = self.render_shell()
        self.assertEqual(html.count('function iniciarTutorial()'), 1)
        self.assertEqual(html.count('id="modalBienvenida"'), 1)
        self.assertIn('const esUsuarioNuevo = true;', html)
        self.assertIn('revision_tutorial', html)

    def test_completed_user_keeps_manual_help_without_being_marked_new(self):
        html = self.render_shell(completed=True)
        self.assertIn('function iniciarTutorial()', html)
        self.assertIn('window.iniciarTutorialSeccion = iniciarTutorialSeccion', html)
        self.assertIn('const esUsuarioNuevo = false;', html)
