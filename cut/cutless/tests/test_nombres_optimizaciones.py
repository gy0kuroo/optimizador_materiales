from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from django.utils.html import escape
from openpyxl import load_workbook

from cutless.exports.excel import generar_excel
from cutless.models import Optimizacion


class NombresOptimizacionesTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('nombres_trabajos')
        self.client.force_login(self.user)
        self.opt = Optimizacion.objects.create(usuario=self.user, ancho_tablero=122,
            alto_tablero=244, piezas='Puerta,40,120,1', nombre='Mueble de cocina')
        self.url = reverse('cutless:renombrar_optimizacion', args=[self.opt.pk])
        self.data = {'unidad_medida':'cm','ancho':122,'alto':244,
            'permitir_rotacion':'on','margen_corte':3,
            'form-TOTAL_FORMS':1,'form-INITIAL_FORMS':0,'form-MIN_NUM_FORMS':0,'form-MAX_NUM_FORMS':20,
            'form-0-nombre':'Puerta','form-0-ancho':40,'form-0-alto':120,'form-0-cantidad':1}

    def test_crear_con_nombre_o_sin_nombre(self):
        for nombre in ['  Mueble   de cocina  ', '']:
            response = self.client.post(reverse('cutless:index'),dict(self.data,nombre_optimizacion=nombre))
            self.assertEqual(response.status_code,200)
            opt = Optimizacion.objects.order_by('-pk').first()
            self.assertEqual(opt.nombre,' '.join(nombre.split()))
            self.assertContains(response,opt.codigo)

    def test_renombrar_solo_cambia_nombre_sin_recalcular(self):
        before=Optimizacion.objects.filter(pk=self.opt.pk).values().get()
        with patch('cutless.views.optimization.generar_grafico') as graph, \
             patch('cutless.views.optimization.persistir_resultado_optimizacion') as persist:
            response=self.client.post(self.url,{'nombre_optimizacion':'Estantería del salón'})
        self.assertRedirects(response,reverse('cutless:resultado',args=[self.opt.pk]),fetch_redirect_response=False)
        graph.assert_not_called();persist.assert_not_called()
        after=Optimizacion.objects.filter(pk=self.opt.pk).values().get()
        self.assertEqual(after.pop('nombre'),'Estantería del salón')
        before.pop('nombre');self.assertEqual(before,after)

    def test_quitar_nombre_conserva_codigo_y_vuelve_al_historial(self):
        code=self.opt.codigo
        response=self.client.post(self.url+'?volver=historial',{'nombre_optimizacion':''})
        self.assertRedirects(response,reverse('cutless:historial'),fetch_redirect_response=False)
        self.opt.refresh_from_db()
        self.assertEqual(self.opt.nombre,'');self.assertEqual(self.opt.etiqueta,code)

    def test_nombre_largo_no_se_guarda(self):
        response=self.client.post(self.url,{'nombre_optimizacion':'x'*101})
        self.assertEqual(response.status_code,200)
        self.assertIn('nombre_optimizacion',response.context['form'].errors)
        self.opt.refresh_from_db();self.assertEqual(self.opt.nombre,'Mueble de cocina')

    def test_solo_propietario_y_con_csrf(self):
        secure=Client(enforce_csrf_checks=True);secure.force_login(self.user)
        self.assertEqual(secure.post(self.url,{'nombre_optimizacion':'Otro'}).status_code,403)
        self.client.force_login(User.objects.create_user('otro_nombre'))
        self.assertEqual(self.client.post(self.url,{'nombre_optimizacion':'Otro'}).status_code,404)

    def test_duplicar_y_editar_cargan_nombre(self):
        for view in ['duplicar_optimizacion','editar_optimizacion']:
            response=self.client.get(reverse('cutless:'+view,args=[self.opt.pk]))
            self.assertEqual(response.context['tablero_form']['nombre_optimizacion'].value(),self.opt.nombre)

    def test_historial_busca_nombre_pieza_y_codigo(self):
        for query in ['cocina','Puerta',self.opt.codigo]:
            response=self.client.get(reverse('cutless:historial'),{'nombre_pieza':query})
            self.assertContains(response,'Mueble de cocina')
            self.assertContains(response,self.opt.codigo)
            self.assertEqual(len(response.context['optimizaciones_con_piezas']),1)

    def test_nombre_es_texto_escapado(self):
        nombre='<script>alert("nombre")</script>'
        self.client.post(self.url,{'nombre_optimizacion':nombre})
        response=self.client.get(reverse('cutless:historial'))
        self.assertContains(response,escape(nombre))
        self.assertNotContains(response,nombre)

    def test_nombre_excel_no_se_convierte_en_formula(self):
        self.opt.nombre='=SUM(1,2)'
        workbook=load_workbook(generar_excel(self.opt,{},[]))
        cell=workbook['Resumen']['B3']
        self.assertEqual(cell.value,self.opt.nombre);self.assertEqual(cell.data_type,'s')
        workbook.close()

    def test_editar_conserva_codigo_y_actualiza_nombre(self):
        response=self.client.post(reverse('cutless:editar_optimizacion',args=[self.opt.pk]),
            dict(self.data,nombre_optimizacion='Cocina renovada'))
        self.assertEqual(response.status_code,200)
        code=self.opt.codigo;self.opt.refresh_from_db()
        self.assertEqual(self.opt.nombre,'Cocina renovada');self.assertEqual(self.opt.codigo,code)
