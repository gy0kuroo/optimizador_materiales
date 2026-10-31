from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class PresentacionInicialTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('presentacion_inicial')
        self.user.perfil.preferencias_menu = {'_inicio_completado': True}
        self.user.perfil.save()
        self.client.force_login(self.user)

    def test_medidas_habituales_ya_presentes_en_html_inicial(self):
        response = self.client.get(reverse('cutless:index'))
        html = response.content.decode()
        self.assertContains(response, 'Usar medidas habituales (opcional)')
        self.assertContains(response, 'Elegir medidas habituales')
        self.assertEqual(html.count('id="tableros-dropdown"'), 1)
        self.assertEqual(html.count('data-medida='), 6)
        self.assertLess(html.index('id="medidas-pred-container"'), html.index('id="unidad_medida_selector"'))
        self.assertContains(response, 'data-ancho-cm="122"')

    def test_opciones_iniciales_en_unidad_del_perfil(self):
        self.user.perfil.unidad_medida_predeterminada = 'm'
        self.user.perfil.save()
        response = self.client.get(reverse('cutless:index'))
        self.assertContains(response, 'OSB (1,22×2,44 m)')
        self.assertContains(response, 'id="dimension-unit-example"')
        self.assertContains(response, '1,22 × 2,44 m. El ancho de sierra siempre se ingresa en mm.')

    def test_iconos_y_logo_incluidos_sin_descargas_o_insercion_tardia(self):
        from html.parser import HTMLParser
        class Assets(HTMLParser):
            def __init__(self):
                super().__init__()
                self.icons = []
                self.images = []
            def handle_starttag(self, tag, attrs):
                attrs = dict(attrs)
                if tag == 'svg':
                    self.icons.append(attrs)
                if tag == 'img':
                    self.images.append(attrs)
        response = self.client.get(reverse('cutless:index'))
        parser = Assets()
        parser.feed(response.content.decode())
        self.assertTrue(any(icon.get('class') == 'brand-symbol' for icon in parser.icons))
        self.assertEqual(sum(icon.get('data-icon') == 'help' for icon in parser.icons), 2)
        self.assertTrue(any('cl-icon--title' in icon.get('class', '') for icon in parser.icons))
        self.assertTrue(any(image.get('src', '').startswith('data:image/png;base64,') for image in parser.images))

    def test_inline_asset_no_permite_rutas_arbitrarias(self):
        from django.template import TemplateSyntaxError
        from cutless.templatetags.initial_assets import inline_asset
        with self.assertRaises(TemplateSyntaxError):
            inline_asset('../../cutless_project/settings.py')

    def test_perfil_oscuro_incluido_antes_de_css(self):
        self.user.perfil.tema_preferido = 'dark'
        self.user.perfil.save()
        response = self.client.get(reverse('cutless:index'))
        self.assertContains(response, '<html lang="es" data-theme="dark">')
        html = response.content.decode()
        self.assertLess(html.index('data-theme-choice'), html.index('<link'))

    def test_perfil_claro_se_mantiene(self):
        self.user.perfil.tema_preferido = 'light'
        self.user.perfil.save()
        self.assertContains(self.client.get(reverse('cutless:index')), '<html lang="es" data-theme="light">')

    def test_ejemplos_iniciales_coinciden_con_la_unidad_sin_cambio_de_puntuacion(self):
        from cutless.forms import TableroForm
        for unit, ancho, alto in [('cm', '122', '244'), ('m', '1,22', '2,44'), ('mm', '1220', '2440')]:
            form = TableroForm(initial={'unidad_medida': unit})
            self.assertEqual(form.fields['ancho'].widget.attrs['placeholder'], f'Ej.: {ancho}')
            self.assertEqual(form.fields['alto'].widget.attrs['placeholder'], f'Ej.: {alto}')
        response = self.client.get(reverse('cutless:index'))
        self.assertContains(response, 'placeholder="Ej.: 122"')
        self.assertNotContains(response, 'placeholder="Ej: 122"')

    def test_lupa_ya_incluye_icono_en_html(self):
        response = self.client.get(reverse('cutless:index'))
        html = response.content.decode()
        bloque = html.split('id="magnifier-toggle"', 1)[1].split('</button>', 1)[0]
        self.assertIn('<svg', bloque)
        self.assertIn('data-icon="search"', bloque)
