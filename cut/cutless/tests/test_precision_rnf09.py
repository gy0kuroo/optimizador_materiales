"""RNF-09: dimensiones, conversiones, sierra y geometría independiente del motor."""
import random
import tempfile
from collections import Counter
from itertools import combinations

from django.contrib.auth.models import User
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from cutless.models import Optimizacion
from cutless.packing import optimizar_corte
from cutless.pieces import parsear_piezas_desde_texto
from cutless.units import convertir_a_cm, convertir_desde_cm


class PrecisionDimensionalTests(SimpleTestCase):
    def comprobar_geometria(self, piezas, rotacion=True, margen=.3):
        tableros, _, info = optimizar_corte(
            piezas, 122, 244, permitir_rotacion=rotacion, margen_corte=margen)
        self.assertEqual(info['num_piezas_colocadas'], sum(p[2] for p in piezas))
        self.assertFalse(info['piezas_no_colocadas'])
        originales = Counter((w, h) for t in tableros for *_, w, h, nombre in t['posiciones'])
        solicitadas = Counter()
        for w, h, cantidad in piezas:
            solicitadas[(w, h)] += cantidad
        self.assertEqual(originales, solicitadas)
        for tablero in tableros:
            for x, y, w, h, girada, original_w, original_h, *_ in tablero['posiciones']:
                self.assertAlmostEqual(w, original_h if girada else original_w, delta=.01)
                self.assertAlmostEqual(h, original_w if girada else original_h, delta=.01)
                self.assertGreaterEqual(x, -1e-8)
                self.assertGreaterEqual(y, -1e-8)
                self.assertLessEqual(x+w, 122+1e-8)
                self.assertLessEqual(y+h, 244+1e-8)
            for a, b in combinations(tablero['posiciones'], 2):
                ax, ay, aw, ah = a[:4]
                bx, by, bw, bh = b[:4]
                gap_x = max(bx-ax-aw, ax-bx-bw)
                gap_y = max(by-ay-ah, ay-by-bh)
                self.assertGreaterEqual(max(gap_x, gap_y), margen-1e-8)
        return tableros

    def test_conversiones_conservan_tolerancia_en_todas_las_unidades(self):
        rng = random.Random(909)
        for unidad in ['cm', 'mm', 'm', 'in', 'ft', 'pulgadas']:
            for valor_cm in [60.9, 130, 122, 244, 39.96, 30.37] + [rng.uniform(.1, 244) for _ in range(200)]:
                with self.subTest(unidad=unidad, cm=valor_cm):
                    vuelta = convertir_a_cm(convertir_desde_cm(valor_cm, unidad), unidad)
                    self.assertAlmostEqual(vuelta, valor_cm, delta=.01)

    def test_sierra_tres_mm_equivale_a_cero_tres_cm(self):
        self.assertEqual(convertir_a_cm(3, 'mm'), .3)
        self.assertEqual(3/10.0, .3)

    def test_dos_piezas_60_9_necesitan_dos_tableros_con_sierra(self):
        self.assertEqual(len(self.comprobar_geometria([(60.9, 130, 2)])), 2)
        self.assertEqual(len(self.comprobar_geometria([(60.9, 130, 2)], margen=0)), 1)
        self.assertEqual(len(self.comprobar_geometria([(60.85, 130, 2)])), 1)

    def test_reserva_de_sierra_alcanza_perimetro_sin_omitir_pieza(self):
        for w, h in [(121.9, 130), (122, 244), (50, 243.9), (121.99, 243.99)]:
            for rotacion in [True, False]:
                with self.subTest(w=w, h=h, rotacion=rotacion):
                    self.assertEqual(len(self.comprobar_geometria([(w, h, 1)], rotacion)), 1)

    def test_casos_aleatorios_y_cincuenta_piezas_sin_solapamientos(self):
        self.comprobar_geometria([(30, 40, 20), (40, 50, 20), (20, 30, 10)])
        rng = random.Random(903)
        for caso in range(500):
            piezas = [(round(rng.uniform(1, 122), 3), round(rng.uniform(1, 244), 3), rng.randint(1, 7))
                      for _ in range(rng.randint(1, 7))]
            with self.subTest(caso=caso):
                self.comprobar_geometria(piezas, rotacion=bool(caso % 2))


class PrecisionEdicionTests(TestCase):
    def test_guardar_y_volver_a_editar_no_altera_dimensiones(self):
        user = User.objects.create_user('precision_guardado')
        self.client.force_login(user)
        with tempfile.TemporaryDirectory(prefix='cutless-rnf09-') as media, override_settings(MEDIA_ROOT=media):
            for unidad in ['m', 'ft']:
                w, h = convertir_desde_cm(60.9, unidad), convertir_desde_cm(130, unidad)
                opt = Optimizacion.objects.create(usuario=user, ancho_tablero=122,
                    alto_tablero=244, unidad_medida=unidad, piezas=f'Puerta,{w},{h},2')
                url = reverse('cutless:editar_optimizacion', args=[opt.pk])
                response = self.client.post(url, {
                    'unidad_medida': unidad,
                    'ancho': convertir_desde_cm(122, unidad),
                    'alto': convertir_desde_cm(244, unidad),
                    'permitir_rotacion': 'on', 'margen_corte': 3,
                    'form-TOTAL_FORMS': 1, 'form-INITIAL_FORMS': 0,
                    'form-0-nombre': 'Puerta', 'form-0-ancho': w,
                    'form-0-alto': h, 'form-0-cantidad': 2,
                })
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, 'cutless/resultado.html')
                opt.refresh_from_db()
                self.assertAlmostEqual(opt.ancho_tablero, 122, delta=.01)
                self.assertAlmostEqual(opt.alto_tablero, 244, delta=.01)
                self.assertEqual(opt.margen_corte, .3)
                self.assertEqual(opt.num_tableros, 2)
                pieza = parsear_piezas_desde_texto(opt.piezas, unidad)[0]
                self.assertAlmostEqual(pieza['ancho_cm'], 60.9, delta=.01)
                self.assertAlmostEqual(pieza['alto_cm'], 130, delta=.01)
                response = self.client.get(url)
                self.assertEqual(response.context['pieza_formset'].forms[0]['ancho'].value(), w)
                self.assertEqual(response.context['pieza_formset'].forms[0]['alto'].value(), h)

    def test_editar_y_duplicar_conservan_unidad_y_dimensiones_originales(self):
        user = User.objects.create_user('precision_rnf09')
        self.client.force_login(user)
        for unidad in ['cm', 'm', 'mm', 'in', 'ft']:
            w = convertir_desde_cm(60.9, unidad)
            h = convertir_desde_cm(130, unidad)
            opt = Optimizacion.objects.create(usuario=user, ancho_tablero=122,
                alto_tablero=244, unidad_medida=unidad, piezas=f'Puerta,{w},{h},2')
            for vista in ['editar_optimizacion', 'duplicar_optimizacion']:
                with self.subTest(unidad=unidad, vista=vista):
                    response = self.client.get(reverse('cutless:'+vista, args=[opt.pk]))
                    self.assertEqual(response.status_code, 200)
                    tablero = response.context['tablero_form']
                    self.assertAlmostEqual(convertir_a_cm(tablero['ancho'].value(), unidad), 122, delta=.01)
                    self.assertAlmostEqual(convertir_a_cm(tablero['alto'].value(), unidad), 244, delta=.01)
                    pieza = response.context['pieza_formset'].forms[0]
                    self.assertEqual(pieza['ancho'].value(), w)
                    self.assertEqual(pieza['alto'].value(), h)
                    self.assertEqual(pieza.fields['ancho'].widget.attrs['step'], 'any')
