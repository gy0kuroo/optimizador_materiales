from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from cutless.models import Optimizacion


class AnalisisTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user('analista')
        self.usuario.perfil.rol = 'admin'
        self.usuario.perfil.save()
        self.client.force_login(self.usuario)

    def crear(self, precio, usuario=None):
        return Optimizacion.objects.create(
            usuario=usuario or self.usuario, ancho_tablero=100, alto_tablero=100,
            piezas='Puerta,20,30,1', precio_tablero=precio, num_tableros=2,
            mano_obra=Decimal('10'), aprovechamiento_total=60,
        )

    def test_diferencia_costos_es_segunda_menos_primera(self):
        primera = self.crear(Decimal('100.50'))
        segunda = self.crear(Decimal('80.25'))
        response = self.client.get(reverse('cutless:comparar_optimizaciones'),
                                   {'opt1': primera.pk, 'opt2': segunda.pk})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['diferencia_costo'], Decimal('-40.50'))
        inversa = self.client.get(reverse('cutless:comparar_optimizaciones'),
                                 {'opt1': segunda.pk, 'opt2': primera.pk})
        self.assertEqual(inversa.context['diferencia_costo'], Decimal('40.50'))

    def test_comparacion_rechaza_mismo_registro_e_id_invalido(self):
        opt = self.crear(Decimal('100'))
        url = reverse('cutless:comparar_optimizaciones')
        for parametros in ({'opt1': opt.pk, 'opt2': opt.pk},
                           {'opt1': 'incorrecto', 'opt2': opt.pk}):
            with self.subTest(parametros=parametros):
                self.assertRedirects(self.client.get(url, parametros), url)

    def test_comparacion_no_expone_registros_ajenos(self):
        propia = self.crear(Decimal('100'))
        ajena = self.crear(Decimal('50'), User.objects.create_user('otroanalista'))
        url = reverse('cutless:comparar_optimizaciones')
        self.assertRedirects(self.client.get(url, {'opt1': propia.pk, 'opt2': ajena.pk}), url)

    def test_costos_incluye_importe_cero_en_detalle_y_promedio(self):
        cero = self.crear(Decimal('0'))
        cero.mano_obra = Decimal('0')
        cero.save()
        self.crear(Decimal('100'))
        self.crear(Decimal('999'), User.objects.create_user('otrocontable'))
        response = self.client.get(reverse('cutless:historial_costos'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_optimizaciones'], 2)
        self.assertEqual(len(response.context['optimizaciones_con_costo']), 2)
        self.assertEqual(response.context['costo_total'], Decimal('210'))
        self.assertEqual(response.context['costo_promedio'], Decimal('105'))
