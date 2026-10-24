import base64
import io
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from PIL import Image

from cutless.models import Optimizacion


class DescargaPngActualTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('png_actual')
        self.client.force_login(self.user)
        self.opt = Optimizacion.objects.create(usuario=self.user, ancho_tablero=122,
            alto_tablero=244, piezas='Puerta,40,120,1')
        self.vista = {'ancho':122, 'alto':244,
            'catalogo':[dict(numero=1, nombre='Puerta', ancho=40, alto=120, cantidad=1, color='#4558E7')],
            'piezas':[dict(x=0, y=0, ancho=40, alto=120, numero=1, nombre='Puerta', color='#4558E7')]}
        old = io.BytesIO(); Image.new('RGB', (20, 40), 'white').save(old, format='PNG')
        self.imagenes = [base64.b64encode(old.getvalue()).decode()]
        self.info = {'info_tableros':[dict(numero=1, vista_web=self.vista, porcentaje_uso=16.12,
                                         num_piezas=1, desperdicio=24968)]}

    def test_ambas_rutas_exportan_png_horizontal_sin_devolver_imagen_antigua(self):
        for route, args in [('descargar_png',[self.opt.pk]), ('descargar_png_tablero',[self.opt.pk,1])]:
            with self.subTest(route=route), patch('cutless.services.optimization.obtener_resultado_optimizacion',
                    return_value=(self.imagenes,16.12,self.info)) as result:
                response = self.client.get(reverse('cutless:'+route,args=args))
                self.assertEqual(response['Content-Type'], 'image/png')
                data = b''.join(response.streaming_content); response.close()
                with Image.open(io.BytesIO(data)) as image:
                    self.assertGreater(image.width, image.height)
                    self.assertGreaterEqual(image.width, 2000)
                self.assertNotEqual(data, base64.b64decode(self.imagenes[0]))
                self.assertFalse(result.call_args.kwargs['persistir_si_falta'])

    def test_tablero_inexistente_no_descarga_otro_tablero(self):
        with patch('cutless.services.optimization.obtener_resultado_optimizacion',
                   return_value=(self.imagenes,16.12,self.info)):
            response = self.client.get(reverse('cutless:descargar_png_tablero',args=[self.opt.pk,2]))
        self.assertRedirects(response, reverse('cutless:historial'), fetch_redirect_response=False)

    def test_otro_usuario_no_puede_descargar(self):
        self.client.force_login(User.objects.create_user('otro_png'))
        response = self.client.get(reverse('cutless:descargar_png',args=[self.opt.pk]))
        self.assertEqual(response.status_code,404)
