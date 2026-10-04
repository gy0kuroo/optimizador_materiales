from datetime import date
from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.test import TestCase, override_settings
from django.urls import reverse

from cutless.exports.pdf import generar_pdf_presupuesto
from cutless.models import Optimizacion, Presupuesto, TableroOptimizacion


class MediaPrivadaTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user('media_user')
        self.otro = User.objects.create_user('media_other')
        self.opt = Optimizacion.objects.create(usuario=self.usuario, ancho_tablero=100, alto_tablero=100, piezas='50,50,1')
        self.opt.imagen.save('media_test.png', ContentFile(b'imagen privada'))
        self.opt.pdf.save('media_test.pdf', ContentFile(b'%PDF-1.4 privado'))
        self.tablero = TableroOptimizacion.objects.create(optimizacion=self.opt, numero=1, area_usada=2500, desperdicio=7500, porcentaje_uso=25)
        self.tablero.imagen.save('media_board_test.png', ContentFile(b'tablero privado'))
        self.url = reverse('media_privada', args=[self.opt.imagen.name])

    def test_anonimo_no_puede_descargar(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('usuarios:login'), response.url)

    def test_propietario_accede_imagen_pdf_y_tablero_sin_cache(self):
        self.client.force_login(self.usuario)
        for archivo, contenido in [(self.opt.imagen, b'imagen privada'), (self.opt.pdf, b'%PDF-1.4 privado'), (self.tablero.imagen, b'tablero privado')]:
            with self.subTest(nombre=archivo.name):
                response = self.client.get(reverse('media_privada', args=[archivo.name]))
                self.assertEqual(response.status_code, 200)
                self.assertEqual(b''.join(response.streaming_content), contenido)
                self.assertIn('private', response['Cache-Control'])
                self.assertIn('no-store', response['Cache-Control'])
                self.assertEqual(response['X-Content-Type-Options'], 'nosniff')
                response.close()

    def test_otro_usuario_y_admin_no_acceden(self):
        self.client.force_login(self.otro)
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.otro.is_superuser = True
        self.otro.save()
        self.assertEqual(self.client.get(self.url).status_code, 404)

    def test_archivo_sin_referencia_o_desconocido_no_se_sirve(self):
        self.client.force_login(self.usuario)
        raiz = Path(settings.MEDIA_ROOT)
        (raiz / 'sin_referencia.pdf').write_bytes(b'no publicar')
        self.assertEqual(self.client.get('/media/sin_referencia.pdf').status_code, 404)
        self.assertEqual(self.client.get('/media/no_existe.pdf').status_code, 404)

    def test_no_se_sirven_bd_rutas_externas_o_post(self):
        self.client.force_login(self.usuario)
        for archivo in ('../db.sqlite3', '../../README.md', 'C:/privado.pdf', 'pdfs/..\\privado.pdf'):
            with self.subTest(archivo=archivo):
                self.assertEqual(self.client.get(reverse('media_privada', args=[archivo])).status_code, 404)
        self.assertEqual(self.client.post(self.url).status_code, 405)

    def test_archivo_referenciado_pero_ausente_da_404(self):
        self.client.force_login(self.usuario)
        Path(self.opt.imagen.path).unlink()
        self.assertEqual(self.client.get(self.url).status_code, 404)

    @override_settings(DEBUG=False, SECURE_SSL_REDIRECT=False)
    def test_media_privada_funciona_sin_debug(self):
        self.client.force_login(self.usuario)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        response.close()

    def test_presupuestos_mismo_numero_tienen_archivos_distintos(self):
        presupuestos = [Presupuesto.objects.create(usuario=usuario, numero='PRE-2026-0001', precio_tablero=100, costo_total=100, fecha_validez=date(2026, 12, 31)) for usuario in (self.usuario, self.otro)]
        presupuestos[0].optimizaciones.add(self.opt)
        primero = generar_pdf_presupuesto(presupuestos[0])
        antes = Path(primero).read_bytes()
        segundo = generar_pdf_presupuesto(presupuestos[1])
        self.assertNotEqual(primero, segundo)
        self.assertEqual(Path(primero).read_bytes(), antes)
        presupuestos[0].pdf = Path(primero).relative_to(settings.MEDIA_ROOT).as_posix()
        presupuestos[0].save()
        self.client.force_login(self.usuario)
        response = self.client.get(reverse('media_privada', args=[presupuestos[0].pdf.name]))
        self.assertEqual(response.status_code, 200)
        response.close()
        self.client.force_login(self.otro)
        self.assertEqual(self.client.get(reverse('media_privada', args=[presupuestos[0].pdf.name])).status_code, 404)

    def test_descarga_presupuesto_guarda_referencia_relativa(self):
        presupuesto = Presupuesto.objects.create(usuario=self.usuario, numero='PRE-2026-0002', precio_tablero=100, costo_total=100, fecha_validez=date(2026, 12, 31))
        presupuesto.optimizaciones.add(self.opt)
        self.client.force_login(self.usuario)
        response = self.client.get(reverse('cutless:generar_pdf_presupuesto', args=[presupuesto.pk]))
        self.assertEqual(response.status_code, 200)
        response.close()
        presupuesto.refresh_from_db()
        self.assertTrue(presupuesto.pdf.name.startswith('presupuestos/'))
        self.assertFalse(Path(presupuesto.pdf.name).is_absolute())
        self.assertTrue(Path(presupuesto.pdf.path).is_file())

    def test_referencia_heredada_compartida_se_bloquea(self):
        Optimizacion.objects.create(usuario=self.otro, ancho_tablero=100, alto_tablero=100, piezas='50,50,1', imagen=self.opt.imagen.name)
        for usuario in (self.usuario, self.otro):
            with self.subTest(usuario=usuario.username):
                self.client.force_login(usuario)
                self.assertEqual(self.client.get(self.url).status_code, 404)
