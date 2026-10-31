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
from cutless.services.optimization import persistir_resultado_optimizacion, obtener_resultado_optimizacion


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
        self.info['info_tableros'][0]['vista_web'] = {
            'ancho': 100, 'alto': 100,
            'catalogo': [{'numero': 1, 'nombre': 'Pieza', 'ancho': 50, 'alto': 50, 'cantidad': 1, 'color': '#FF6B6B'}],
            'piezas': [{'x': 0, 'y': 0, 'ancho': 50, 'alto': 50, 'numero': 1, 'nombre': 'Pieza', 'color': '#FF6B6B'}],
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

    def test_guardar_no_escribe_archivos_ni_genera_pdf(self):
        with patch.object(self.opt.imagen.storage, 'save', side_effect=AssertionError('No escribir')):
            with patch('cutless.services.optimization.generar_pdf', side_effect=AssertionError('No PDF')):
                persistir_resultado_optimizacion(self.opt, self.imagenes, self.info, 25)
        self.opt.refresh_from_db()
        self.assertFalse(self.opt.pdf)
        self.assertFalse(self.opt.imagen)
        self.assertFalse(self.opt.tableros.get().imagen)
        self.assertEqual(self.archivos(), self.antes)

    def test_vista_web_se_guarda_y_se_recupera_sin_recalcular(self):
        from cutless.services.optimization import obtener_resultado_optimizacion
        vista = self.info['info_tableros'][0]['vista_web']
        self.info['info_tableros'][0]['vista_web'] = vista
        persistir_resultado_optimizacion(self.opt, self.imagenes, self.info, 25)
        self.opt.refresh_from_db()
        self.assertEqual(self.opt.resultado_extra['vistas_web']['1'], vista)
        with patch('cutless.services.optimization._regenerar_grafico', side_effect=AssertionError('No recalcular')):
            _, _, info = obtener_resultado_optimizacion(self.opt)
        self.assertEqual(info['info_tableros'][0]['vista_web'], vista)

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

    def test_fallo_creacion_no_deja_registro(self):
        nuevo = Optimizacion(usuario=self.usuario, ancho_tablero=100, alto_tablero=100, piezas='50,50,1')
        with patch.object(TableroOptimizacion, 'save', side_effect=IntegrityError('BD fallida')):
            with self.assertRaises(IntegrityError):
                persistir_resultado_optimizacion(nuevo, self.imagenes, self.info, 25)
        self.assertIsNone(nuevo.pk)
        self.assertEqual(Optimizacion.objects.count(), 1)
        self.comprobar_anterior()

    def test_fallo_creacion_desde_vista_no_deja_registro(self):
        with patch.object(TableroOptimizacion, 'save', side_effect=IntegrityError('BD fallida')):
            with self.assertRaises(IntegrityError):
                self.client.post(reverse('cutless:index'), self.post)
        self.assertEqual(Optimizacion.objects.count(), 1)
        self.comprobar_anterior()

    def test_fallo_edicion_desde_vista_conserva_parametros(self):
        with patch.object(TableroOptimizacion, 'save', side_effect=IntegrityError('BD fallida')):
            with self.assertRaises(IntegrityError):
                self.client.post(reverse('cutless:editar_optimizacion', args=[self.opt.pk]), self.post)
        self.comprobar_anterior()

    def test_exportaciones_no_recalculan_ni_escriben_y_restringen_propietario(self):
        antes = Optimizacion.objects.filter(pk=self.opt.pk).values().get()
        with patch('cutless.services.optimization._regenerar_grafico', side_effect=AssertionError('No recalcular')):
            with patch.object(self.opt.imagen.storage, 'save', side_effect=AssertionError('No escribir')):
                for ruta in ('descargar_pdf', 'descargar_png', 'descargar_excel', 'imprimir_plan_corte', 'api_tableros'):
                    with self.subTest(ruta=ruta):
                        response = self.client.get(reverse('cutless:' + ruta, args=[self.opt.pk]))
                        self.assertEqual(response.status_code, 200)
                        if response.streaming:
                            contenido = b''.join(response.streaming_content)
                            self.assertTrue(contenido)
                        response.close()
                response = self.client.get(reverse('cutless:historial'))
                self.assertContains(response, 'chart-thumbnail-horizontal')
        self.assertEqual(Optimizacion.objects.filter(pk=self.opt.pk).values().get(), antes)
        self.assertEqual(self.archivos(), self.antes)
        otro = User.objects.create_user('otro_sin_archivos')
        self.client.force_login(otro)
        for ruta in ('descargar_pdf', 'descargar_png', 'descargar_excel', 'imprimir_plan_corte', 'api_tableros'):
            self.assertEqual(self.client.get(reverse('cutless:' + ruta, args=[self.opt.pk])).status_code, 404)

    def test_datos_invalidos_no_alteran_resultado(self):
        for imagenes, info in [([], self.info), (['!base64!'], self.info), (self.imagenes, {})]:
            with self.subTest(imagenes=imagenes):
                with self.assertRaises(ValueError):
                    persistir_resultado_optimizacion(self.opt, imagenes, info, 25)
                self.comprobar_anterior()


    def test_resultado_sin_geometria_ni_archivos_no_se_recalcula(self):
        self.opt.resultado_extra = {}
        self.opt.save(update_fields=['resultado_extra'])
        with patch('cutless.services.optimization._regenerar_grafico', side_effect=AssertionError('No recalcular')):
            with self.assertRaisesMessage(ValueError, 'no tiene coordenadas'):
                obtener_resultado_optimizacion(self.opt)

    def test_pdf_y_png_son_formatos_validos_desde_datos_guardados(self):
        for ruta, firma in (('descargar_pdf', b'%PDF'), ('descargar_png', b'\x89PNG')):
            response = self.client.get(reverse('cutless:' + ruta, args=[self.opt.pk]))
            self.assertTrue(b''.join(response.streaming_content).startswith(firma))
            response.close()
        self.comprobar_anterior()
