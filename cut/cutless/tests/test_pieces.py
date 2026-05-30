from django.test import TestCase

from cutless.pieces import parsear_piezas_desde_texto


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
