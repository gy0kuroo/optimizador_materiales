import json
import re

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from cutless.models import Material, Optimizacion, Plantilla


class MaterialesJsonTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user('json_user')
        self.client.force_login(self.usuario)
        self.nombre = '</script><script>alert("xss")</script>& MDF ñ'
        self.material = Material.objects.create(
            usuario=self.usuario, nombre=self.nombre, ancho=122, alto=244, precio='12000.00',
        )
        otro = User.objects.create_user('json_other')
        self.ajeno = Material.objects.create(usuario=otro, nombre='Privado', ancho=122, alto=244)
        self.sistema = Material.objects.create(nombre='Sistema', ancho=122, alto=244, es_predefinido=True)

    def comprobar_datos(self, response):
        self.assertEqual(response.status_code, 200)
        html = response.content.decode('utf-8')
        bloques = re.findall(r'<script id="materiales-data" type="application/json">(.*?)</script>', html, re.S)
        self.assertEqual(len(bloques), 1)
        contenido = bloques[0]
        self.assertNotIn('<', contenido)
        self.assertNotIn('>', contenido)
        self.assertNotIn('&', contenido)
        datos = json.loads(contenido)
        self.assertIsInstance(datos, dict)
        self.assertEqual(datos[str(self.material.pk)]['nombre'], self.nombre)
        self.assertEqual(datos[str(self.material.pk)]['precio'], 12000.0)
        self.assertNotIn(str(self.ajeno.pk), datos)
        self.assertIn(str(self.sistema.pk), datos)
        self.assertIn("JSON.parse(document.getElementById('materiales-data').textContent)", html)
        self.assertNotIn(self.nombre, html)

    def test_index_serializa_materiales_sin_codigo_ejecutable(self):
        self.comprobar_datos(self.client.get(reverse('cutless:index')))

    def test_editar_serializa_materiales_sin_codigo_ejecutable(self):
        opt = Optimizacion.objects.create(usuario=self.usuario, ancho_tablero=122, alto_tablero=244, piezas='50,50,1')
        self.comprobar_datos(self.client.get(reverse('cutless:editar_optimizacion', args=[opt.pk])))

    def test_plantilla_serializa_materiales_sin_codigo_ejecutable(self):
        plantilla = Plantilla.objects.create(usuario=self.usuario, nombre='Prueba', ancho_tablero=122, alto_tablero=244, piezas='50,50,1')
        self.comprobar_datos(self.client.get(reverse('cutless:usar_plantilla', args=[plantilla.pk])))

    def test_index_invalido_conserva_json_seguro(self):
        self.comprobar_datos(self.client.post(reverse('cutless:index'), {
            'ancho': '', 'alto': '', 'unidad_medida': 'cm',
            'form-TOTAL_FORMS': 0, 'form-INITIAL_FORMS': 0,
        }))

    def test_editar_invalido_conserva_json_seguro(self):
        opt = Optimizacion.objects.create(usuario=self.usuario, ancho_tablero=122, alto_tablero=244, piezas='50,50,1')
        self.comprobar_datos(self.client.post(reverse('cutless:editar_optimizacion', args=[opt.pk]), {
            'ancho': '', 'alto': '', 'unidad_medida': 'cm',
            'form-TOTAL_FORMS': 0, 'form-INITIAL_FORMS': 0,
        }))
