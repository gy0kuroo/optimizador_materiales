from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.db import IntegrityError
from django.test import TestCase

from .models import Presupuesto
from .utils import parsear_piezas_desde_texto


class ParsearPiezasTests(TestCase):
    def test_formato_con_nombre(self):
        texto = "Puerta,80,200,2\nCajon,40,50,4"
        piezas = parsear_piezas_desde_texto(texto, 'cm')

        self.assertEqual(len(piezas), 2)
        self.assertEqual(piezas[0]['nombre'], 'Puerta')
        self.assertEqual(piezas[0]['cantidad'], 2)
        self.assertEqual(piezas[0]['ancho_cm'], 80.0)

    def test_formato_legacy_tres_campos(self):
        texto = "80,200,2\n40,50,1"
        piezas = parsear_piezas_desde_texto(texto, 'cm')

        self.assertEqual(len(piezas), 2)
        self.assertEqual(piezas[0]['nombre'], 'Pieza 1')
        self.assertEqual(piezas[0]['ancho'], 80.0)
        self.assertEqual(piezas[0]['alto'], 200.0)
        self.assertEqual(piezas[0]['cantidad'], 2)
        self.assertEqual(piezas[1]['nombre'], 'Pieza 2')

    def test_lineas_invalidas_se_ignoran(self):
        texto = "malformado\n80,200,2"
        piezas = parsear_piezas_desde_texto(texto, 'cm')
        self.assertEqual(len(piezas), 1)


class PresupuestoNumeroTests(TestCase):
    def setUp(self):
        self.usuario_a = User.objects.create_user('usuario_a', password='test12345')
        self.usuario_b = User.objects.create_user('usuario_b', password='test12345')
        self.fecha_validez = date.today()

    def _crear_presupuesto(self, usuario, numero):
        return Presupuesto.objects.create(
            usuario=usuario,
            numero=numero,
            precio_tablero=Decimal('10000'),
            mano_obra=Decimal('0'),
            costo_total=Decimal('10000'),
            fecha_validez=self.fecha_validez,
        )

    def test_mismo_numero_en_distintos_usuarios(self):
        numero = Presupuesto.generar_numero_presupuesto(usuario=self.usuario_a)
        self._crear_presupuesto(self.usuario_a, numero)
        self._crear_presupuesto(self.usuario_b, numero)

        self.assertEqual(
            Presupuesto.objects.filter(numero=numero).count(),
            2,
        )

    def test_numero_duplicado_mismo_usuario_falla(self):
        numero = Presupuesto.generar_numero_presupuesto(usuario=self.usuario_a)
        self._crear_presupuesto(self.usuario_a, numero)

        with self.assertRaises(IntegrityError):
            self._crear_presupuesto(self.usuario_a, numero)

    def test_generador_incrementa_por_usuario(self):
        primero = Presupuesto.generar_numero_presupuesto(usuario=self.usuario_a)
        self._crear_presupuesto(self.usuario_a, primero)
        segundo = Presupuesto.generar_numero_presupuesto(usuario=self.usuario_a)

        self.assertNotEqual(primero, segundo)
