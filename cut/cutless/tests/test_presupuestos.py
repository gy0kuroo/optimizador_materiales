from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.db import IntegrityError
from django.test import TestCase

from cutless.models import Presupuesto


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
