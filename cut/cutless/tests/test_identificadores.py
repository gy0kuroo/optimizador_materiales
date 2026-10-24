import base64
import io
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from openpyxl import load_workbook
from PIL import Image

from cutless.models import Optimizacion
from cutless.services.optimization import (
    calcular_numero_lista, nombre_descarga_pdf, nombre_descarga_png_tablero,
    nombre_descarga_excel,
)


class IdentificadoresPermanentesTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('referencias')
        self.client.force_login(self.user)
        self.opts = [Optimizacion.objects.create(usuario=self.user, ancho_tablero=122,
            alto_tablero=244, piezas=f'Puerta {i},40,120,1', aprovechamiento_total=i*10)
            for i in range(1,8)]

    def test_eliminar_intermedia_no_renumera_ordenes_ni_filtros(self):
        before = {o.pk:o.codigo for o in self.opts}
        self.opts[4].delete()
        for order in ['fecha_desc','fecha_asc','aprovechamiento_desc','aprovechamiento_asc']:
            response = self.client.get(reverse('cutless:historial'), {'ordenar_por':order})
            self.assertEqual(response.status_code,200)
            for item in response.context['optimizaciones_con_piezas']:
                opt = item['optimizacion']
                self.assertEqual(item['numero'],opt.pk)
                self.assertContains(response,before[opt.pk])
                self.assertEqual(calcular_numero_lista(self.user,opt.pk,order),opt.pk)
        response = self.client.get(reverse('cutless:historial'), {'nombre_pieza':'Puerta 6'})
        self.assertContains(response,self.opts[5].codigo)
        self.assertEqual(len(response.context['optimizaciones_con_piezas']),1)

    def test_eliminar_ultima_no_reutiliza_codigo(self):
        last_id = self.opts[-1].pk
        self.opts[-1].delete()
        new = Optimizacion.objects.create(usuario=self.user,ancho_tablero=122,
            alto_tablero=244,piezas='Puerta,40,120,1')
        self.assertGreater(new.pk,last_id)
        self.assertEqual(new.codigo,f'OPT-{new.pk:04d}')

    def test_descargas_ignoran_posicion_y_distinguen_tableros(self):
        opt = self.opts[5]
        self.assertEqual(nombre_descarga_pdf(1,opt),opt.codigo+'.pdf')
        self.assertEqual(nombre_descarga_excel(999,opt),opt.codigo+'.xlsx')
        self.assertEqual(nombre_descarga_png_tablero(1,opt,2),opt.codigo+'_tablero-2.png')

    def test_duplicar_y_eliminar_utilizan_la_misma_referencia(self):
        opt=self.opts[5]
        response=self.client.get(reverse('cutless:duplicar_optimizacion',args=[opt.pk]))
        self.assertContains(response,opt.codigo)
        response=self.client.get(reverse('cutless:borrar_optimizacion',args=[opt.pk]))
        self.assertContains(response,opt.codigo)

    def test_contenido_pdf_y_excel_identifica_el_trabajo(self):
        from cutless.exports.excel import generar_excel
        from cutless.exports.pdf import generar_pdf
        from reportlab.pdfgen.canvas import Canvas
        opt=self.opts[5]
        info={'info_tableros':[], 'area_usada_total':4800,'desperdicio_total':24968}
        workbook=load_workbook(generar_excel(opt,info,[],numero_lista=1))
        self.assertIn(opt.codigo,workbook['Resumen']['A1'].value)
        workbook.close()
        png=io.BytesIO();Image.new('RGB',(20,40),'white').save(png,format='PNG')
        original=Canvas.drawCentredString
        labels=[]
        def capture(canvas,x,y,text,*args,**kwargs):
            labels.append(text)
            return original(canvas,x,y,text,*args,**kwargs)
        with patch.object(Canvas,'drawCentredString',autospec=True,side_effect=capture):
            generar_pdf(opt,[base64.b64encode(png.getvalue()).decode()],numero_lista=1,
                info_desperdicio=info,archivo_salida=io.BytesIO())
        self.assertTrue(any(opt.codigo in text for text in labels))
