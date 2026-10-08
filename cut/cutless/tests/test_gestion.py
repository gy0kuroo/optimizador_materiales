from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from cutless.forms import MaterialForm
from cutless.models import Cliente, Material, Optimizacion, Presupuesto, Proyecto


class GestionTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user('gestor')
        self.usuario.perfil.rol = 'admin'
        self.usuario.perfil.save()
        self.client.force_login(self.usuario)

    def test_material_en_metros_se_guarda_en_cm_y_se_edita_sin_escalar_otra_vez(self):
        datos = {'nombre': 'MDF', 'ancho': '1.22', 'alto': '2.44',
                 'unidad_medida': 'm', 'precio': '0', 'descripcion': ''}
        self.client.post(reverse('cutless:crear_material'), datos)
        material = Material.objects.get(usuario=self.usuario)
        self.assertAlmostEqual(material.ancho, 122)
        self.assertAlmostEqual(material.alto, 244)
        self.assertEqual(material.get_area(), 122 * 244)
        form = MaterialForm(instance=material)
        self.assertAlmostEqual(form['ancho'].value(), 1.22)
        self.client.post(reverse('cutless:editar_material', args=[material.pk]), datos)
        material.refresh_from_db()
        self.assertAlmostEqual(material.ancho, 122)
        response = self.client.get(reverse('cutless:lista_materiales'))
        self.assertNotContains(response, 'Sin precio')

    def test_material_no_acepta_cero_negativo_o_medidas_no_finitas(self):
        datos = {'nombre': 'Tablero', 'ancho': '100', 'alto': '200', 'unidad_medida': 'cm'}
        for cambio in ({'ancho': '0'}, {'alto': '-1'}, {'ancho': 'nan'}, {'precio': '-1'}):
            with self.subTest(cambio=cambio):
                self.assertFalse(MaterialForm({**datos, **cambio}).is_valid())

    def test_listas_y_formularios_sin_registros_se_renderizan(self):
        for grupo in ('presupuestos', 'proyectos', 'clientes', 'materiales'):
            with self.subTest(grupo=grupo):
                self.assertEqual(self.client.get(reverse('cutless:lista_' + grupo)).status_code, 200)
        for tipo in ('presupuesto', 'proyecto', 'cliente', 'material'):
            with self.subTest(tipo=tipo):
                self.assertEqual(self.client.get(reverse('cutless:crear_' + tipo)).status_code, 200)

    def test_detalles_edicion_y_seleccion_con_registros_se_renderizan(self):
        cliente = Cliente.objects.create(usuario=self.usuario, nombre='Cliente de prueba')
        proyecto = Proyecto.objects.create(usuario=self.usuario, cliente=cliente, nombre='Cocina')
        opt = Optimizacion.objects.create(usuario=self.usuario, ancho_tablero=122,
                                         alto_tablero=244, piezas='Puerta,40,50,1',
                                         precio_tablero=0, num_tableros=1)
        presupuesto = Presupuesto.objects.create(usuario=self.usuario, cliente=cliente,
                                                numero='PRUEBA', precio_tablero=0,
                                                costo_total=0, fecha_validez=date(2030, 1, 1))
        presupuesto.optimizaciones.add(opt)
        cliente_sin_relaciones = Cliente.objects.create(usuario=self.usuario, nombre='Sin asociaciones')
        rutas = [('detalle_presupuesto', presupuesto.pk), ('editar_presupuesto', presupuesto.pk),
                 ('detalle_proyecto', proyecto.pk), ('editar_proyecto', proyecto.pk),
                 ('historial_cliente', cliente.pk), ('editar_cliente', cliente.pk),
                 ('agregar_optimizaciones_proyecto', proyecto.pk),
                 ('agregar_optimizaciones_presupuesto', presupuesto.pk),
                 ('eliminar_cliente', cliente_sin_relaciones.pk), ('eliminar_proyecto', proyecto.pk)]
        for nombre, pk in rutas:
            with self.subTest(ruta=nombre):
                self.assertEqual(self.client.get(reverse('cutless:' + nombre, args=[pk])).status_code, 200)
