import base64
import io
from pathlib import Path
from unittest.mock import patch

from PIL import Image
from django.conf import settings
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.test import TransactionTestCase
from django.urls import reverse

from cutless.models import Optimizacion, TableroOptimizacion
from cutless.services.optimization import persistir_resultado_optimizacion, _generar_y_guardar_pdf


class PersistenciaResultadoTests(TransactionTestCase):
    def setUp(self):
        self.usuario = User.objects.create_user('persist_user')
        self.client.force_login(self.usuario)
        png = io.BytesIO()
        Image.new('RGB', (2, 2), 'white').save(png, format='PNG')
        self.imagenes = [base64.b64encode(png.getvalue()).decode('ascii')]
        self.info = {
            'area_usada_total': 2500, 'desperdicio_total': 7500,
            'info_tableros': [{'numero': 1, 'area_usada': 2500, 'desperdicio': 7500, 'porcentaje_uso': 25, 'num_piezas': 1}],
            'num_tableros': 1, 'num_piezas_solicitadas': 1, 'num_piezas_colocadas': 1,
        }
        self.opt = Optimizacion(usuario=self.usuario, ancho_tablero=100, alto_tablero=100, piezas='50,50,1')
        persistir_resultado_optimizacion(self.opt, self.imagenes, self.info, 25)
        self.antes = self.archivos()
        self.datos = Optimizacion.objects.filter(pk=self.opt.pk).values().get()
        self.tableros = list(self.opt.tableros.values())
        self.post = {
            'unidad_medida': 'cm', 'ancho': 100, 'alto': 100,
            'permitir_rotacion': 'on', 'margen_corte': 0,
            'form-TOTAL_FORMS': 1, 'form-INITIAL_FORMS': 0,
            'form-0-nombre': 'Nueva', 'form-0-ancho': 40, 'form-0-alto': 40, 'form-0-cantidad': 1,
        }

    def archivos(self):
        return {str(p): p.read_bytes() for p in Path(settings.MEDIA_ROOT).rglob('*') if p.is_file()}

    def comprobar_anterior(self):
        self.assertEqual(Optimizacion.objects.filter(pk=self.opt.pk).values().get(), self.datos)
        self.assertEqual(list(self.opt.tableros.values()), self.tableros)
        self.assertEqual(self.archivos(), self.antes)

    def test_fallo_pdf_conserva_resultado_y_retira_nuevos(self):
        self.opt.piezas = '40,40,1'
        with patch('cutless.services.optimization.generar_pdf', side_effect=OSError('PDF fallido')):
            with self.assertRaises(OSError):
                persistir_resultado_optimizacion(self.opt, self.imagenes, self.info, 25)
        self.comprobar_anterior()
        self.assertEqual(self.opt.piezas, '50,50,1')

    def test_fallo_guardado_pdf_conserva_anterior(self):
        storage = self.opt.pdf.storage
        original = storage.save
        def guardar(nombre, contenido, *args, **kwargs):
            if nombre.endswith('.pdf'):
                raise OSError('Sin espacio para PDF')
            return original(nombre, contenido, *args, **kwargs)
        with patch.object(storage, 'save', side_effect=guardar):
            with self.assertRaises(OSError):
                persistir_resultado_optimizacion(self.opt, self.imagenes, self.info, 25)
        self.comprobar_anterior()

    def test_escritura_parcial_se_retira(self):
        storage = self.opt.imagen.storage
        original = storage.save
        def guardar(nombre, contenido, *args, **kwargs):
            original(nombre, contenido, *args, **kwargs)
            raise OSError('Escritura interrumpida')
        with patch.object(storage, 'save', side_effect=guardar):
            with self.assertRaises(OSError):
                persistir_resultado_optimizacion(self.opt, self.imagenes, self.info, 25)
        self.comprobar_anterior()

    def test_fallo_tablero_revierte_borrado_y_retira_archivos(self):
        with patch.object(TableroOptimizacion, 'save', side_effect=IntegrityError('BD fallida')):
            with self.assertRaises(IntegrityError):
                persistir_resultado_optimizacion(self.opt, self.imagenes, self.info, 25)
        self.comprobar_anterior()

    def test_fallo_guardado_final_revierte_resultado(self):
        with patch.object(Optimizacion, 'save', side_effect=IntegrityError('BD fallida')):
            with self.assertRaises(IntegrityError):
                persistir_resultado_optimizacion(self.opt, self.imagenes, self.info, 25)
        self.comprobar_anterior()

    def test_reemplazo_completo_retira_archivos_anteriores(self):
        antiguos = [self.opt.imagen.path, self.opt.pdf.path, self.opt.tableros.get().imagen.path]
        persistir_resultado_optimizacion(self.opt, self.imagenes, self.info, 25)
        self.opt.refresh_from_db()
        self.assertTrue(self.opt.resultado_generado)
        self.assertEqual(self.opt.tableros.count(), 1)
        self.assertTrue(Path(self.opt.pdf.path).is_file())
        self.assertTrue(Path(self.opt.imagen.path).is_file())
        for nombre in antiguos:
            self.assertFalse(Path(nombre).exists())

    def test_fallo_creacion_no_deja_registro(self):
        nuevo = Optimizacion(usuario=self.usuario, ancho_tablero=100, alto_tablero=100, piezas='50,50,1')
        with patch('cutless.services.optimization.generar_pdf', side_effect=OSError('PDF fallido')):
            with self.assertRaises(OSError):
                persistir_resultado_optimizacion(nuevo, self.imagenes, self.info, 25)
        self.assertIsNone(nuevo.pk)
        self.assertEqual(Optimizacion.objects.count(), 1)
        self.comprobar_anterior()

    def test_fallo_creacion_desde_vista_no_deja_registro(self):
        with patch('cutless.services.optimization.generar_pdf', side_effect=OSError('PDF fallido')):
            with self.assertRaises(OSError):
                self.client.post(reverse('cutless:index'), self.post)
        self.assertEqual(Optimizacion.objects.count(), 1)
        self.comprobar_anterior()

    def test_fallo_edicion_desde_vista_conserva_parametros(self):
        with patch('cutless.services.optimization.generar_pdf', side_effect=OSError('PDF fallido')):
            with self.assertRaises(OSError):
                self.client.post(reverse('cutless:editar_optimizacion', args=[self.opt.pk]), self.post)
        self.comprobar_anterior()

    def test_pdf_mismo_numero_otro_usuario_no_sobrescribe(self):
        otro = User.objects.create_user('persist_other')
        nuevo = Optimizacion(usuario=otro, ancho_tablero=100, alto_tablero=100, piezas='50,50,1')
        persistir_resultado_optimizacion(nuevo, self.imagenes, self.info, 25, numero_lista=1)
        self.assertNotEqual(nuevo.pdf.name, self.opt.pdf.name)
        for archivo, contenido in self.antes.items():
            self.assertEqual(Path(archivo).read_bytes(), contenido)

    def test_fallo_regeneracion_pdf_conserva_anterior(self):
        with patch('cutless.services.optimization.generar_pdf', side_effect=OSError('PDF fallido')):
            with self.assertRaises(OSError):
                _generar_y_guardar_pdf(self.opt, self.imagenes, self.info)
        self.comprobar_anterior()

    def test_datos_invalidos_no_alteran_resultado(self):
        for imagenes, info in [([], self.info), (['!base64!'], self.info), (self.imagenes, {})]:
            with self.subTest(imagenes=imagenes):
                with self.assertRaises(ValueError):
                    persistir_resultado_optimizacion(self.opt, imagenes, info, 25)
                self.comprobar_anterior()

    def test_regeneracion_pdf_fallo_bd_conserva_archivo(self):
        with patch.object(Optimizacion, 'save', side_effect=IntegrityError('BD fallida')):
            with self.assertRaises(IntegrityError):
                _generar_y_guardar_pdf(self.opt, self.imagenes, self.info)
        self.comprobar_anterior()

    def test_regeneracion_pdf_exitosa_retira_solo_pdf_anterior(self):
        anterior = self.opt.pdf.path
        imagen = self.opt.imagen.path
        ruta = _generar_y_guardar_pdf(self.opt, self.imagenes, self.info)
        self.opt.refresh_from_db()
        self.assertEqual(ruta, self.opt.pdf.path)
        self.assertTrue(Path(ruta).exists())
        self.assertFalse(Path(anterior).exists())
        self.assertTrue(Path(imagen).exists())
        self.assertEqual(list(self.opt.tableros.values()), self.tableros)

    def test_fallo_limpieza_se_registra_sin_revertir_resultado(self):
        with patch.object(self.opt.imagen.storage, 'delete', side_effect=OSError('Limpieza bloqueada')):
            with self.assertLogs('cutless.services.optimization', level='ERROR'):
                persistir_resultado_optimizacion(self.opt, self.imagenes, self.info, 25)
        self.opt.refresh_from_db()
        self.assertNotEqual(self.opt.pdf.name, self.datos['pdf'])
        self.assertTrue(Path(self.opt.pdf.path).exists())
        self.assertTrue(self.opt.resultado_generado)
