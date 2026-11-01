"""Condiciones del menú y herencia de bloques al separar la plantilla base."""
from types import SimpleNamespace
from django.template import Context, Engine
from django.test import SimpleTestCase
from django.urls import reverse

class ShellNavigationTests(SimpleTestCase):
    def render_shell(self, authenticated=True, enabled=False, admin=False, route='index', child=False):
        profile=SimpleNamespace(tutorial_completado=True,tema_preferido='dark',tamanio_fuente='normal',
            rol='admin' if admin else 'usuario',get_timeout_segundos_str='1800',
            menu_visible={key:enabled for key in ['gestion','analisis','materiales','clientes','proyectos','presupuestos','plantillas','costos','comparar','estadisticas']})
        user=SimpleNamespace(is_authenticated=authenticated,is_superuser=admin,username='revision_menu',perfil=profile)
        engine=Engine.get_default()
        template=engine.from_string('{% extends "cutless/base.html" %}{% block show_auth_buttons %}<span id="custom-auth">Acceso específico</span>{% endblock %}') if child else engine.get_template('cutless/base.html')
        return template.render(Context({'user':user,'csrf_token':'revision',
            'request':SimpleNamespace(resolver_match=SimpleNamespace(url_name=route))}))

    def test_child_can_still_override_auth_buttons_and_anonymous_has_no_magnifier(self):
        html=self.render_shell(authenticated=False,child=True)
        self.assertIn('id="custom-auth"',html)
        self.assertNotIn('href="'+reverse('usuarios:registro')+'"',html)
        self.assertNotIn('id="reading-magnifier"',html)

    def test_limited_menu_keeps_basic_links_without_optional_groups(self):
        html=self.render_shell()
        self.assertIn('href="'+reverse('cutless:index')+'"',html)
        self.assertIn('href="'+reverse('cutless:historial')+'"',html)
        self.assertNotIn('id="nav-gestion"',html)
        self.assertNotIn('id="nav-analisis"',html)
        self.assertEqual(html.count('id="reading-magnifier"'),1)
        self.assertEqual(html.count('id="magnifier-toggle"'),1)

    def test_active_group_and_admin_link_follow_the_same_conditions(self):
        html=self.render_shell(enabled=True,route='lista_materiales')
        self.assertIn('<details class="nav-group" open>',html)
        self.assertIn('aria-current="page" href="'+reverse('cutless:lista_materiales')+'"',html)
        self.assertNotIn('href="'+reverse('usuarios:admin_dashboard')+'"',html)
        admin=self.render_shell(enabled=True,admin=True,route='admin_dashboard')
        self.assertIn('href="'+reverse('usuarios:admin_dashboard')+'"',admin)
