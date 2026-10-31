from datetime import date
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from cutless.forms import PlantillaForm, MaterialForm, ClienteForm, ProyectoForm, PresupuestoForm
from cutless.models import Cliente, Optimizacion, Plantilla, Proyecto


class RevisionHerramientasTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('revision-herramientas')
        self.user.perfil.rol = 'admin'
        self.user.perfil.save()
        self.client.force_login(self.user)
        self.template = dict(nombre='Armario', categoria='muebles', ancho_tablero=122,
                             alto_tablero=244, unidad_medida='cm', margen_corte=3,
                             permitir_rotacion='on', piezas='Puerta,60,130,2')

    def test_template_rejects_invalid_dimensions_quantities_and_fit(self):
        casos = [dict(ancho_tablero=100000), dict(piezas='P,500,30,1'),
                 dict(piezas='P,20,30,101'), dict(piezas='P,20,30,1\n' * 21),
                 dict(piezas='P,130,245,1'), dict(piezas='P,0.01,30,1')]
        for cambio in casos:
            with self.subTest(cambio=cambio):
                form = PlantillaForm({**self.template, **cambio}, user=self.user)
                self.assertFalse(form.is_valid())

    def test_template_fit_respects_rotation(self):
        data = {**self.template, 'piezas': 'P,200,100,1'}
        self.assertTrue(PlantillaForm(data, user=self.user).is_valid())
        data.pop('permitir_rotacion')
        self.assertFalse(PlantillaForm(data, user=self.user).is_valid())

    def test_invalid_saved_template_is_not_loaded_into_optimizer(self):
        template = Plantilla.objects.create(usuario=self.user, nombre='Antigua',
                    ancho_tablero=10000, alto_tablero=244, piezas='P,20,30,1')
        response = self.client.get(reverse('cutless:usar_plantilla', args=[template.pk]))
        self.assertTemplateUsed(response, 'cutless/editar_plantilla.html')
        self.assertTrue(response.context['form'].errors)
        template.refresh_from_db()
        self.assertEqual(template.ancho_tablero, 10000)

    def test_material_rejects_same_physical_limit_in_all_units(self):
        for unit, width in [('cm', 301), ('m', 3.01), ('in', 120), ('ft', 10)]:
            form = MaterialForm(dict(nombre='OSB', ancho=width, alto=width, unidad_medida=unit))
            self.assertFalse(form.is_valid())

    def test_duplicate_client_is_form_error_and_other_owner_is_allowed(self):
        Cliente.objects.create(usuario=self.user, nombre='Carpintería')
        self.assertFalse(ClienteForm({'nombre': 'Carpintería'}, user=self.user).is_valid())
        other = User.objects.create_user('otra-persona')
        self.assertTrue(ClienteForm({'nombre': 'Carpintería'}, user=other).is_valid())

    def test_project_rejects_inverted_dates(self):
        form = ProyectoForm(dict(nombre='Cocina', estado='planificacion',
                            fecha_inicio='2030-02-10', fecha_fin='2030-02-01'), user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('fecha_fin', form.errors)

    def test_project_does_not_move_another_projects_plan(self):
        original = Proyecto.objects.create(usuario=self.user, nombre='Original')
        target = Proyecto.objects.create(usuario=self.user, nombre='Destino')
        opt = Optimizacion.objects.create(usuario=self.user, proyecto=original,
              ancho_tablero=122, alto_tablero=244, piezas='P,20,30,1', num_tableros=1)
        self.client.post(reverse('cutless:agregar_optimizaciones_proyecto', args=[target.pk]),
                         {'optimizaciones': [opt.pk]})
        opt.refresh_from_db()
        self.assertEqual(opt.proyecto_id, original.pk)

    def test_budget_rejects_negative_cost_and_conflicting_client(self):
        client = Cliente.objects.create(usuario=self.user, nombre='Cliente')
        opt = Optimizacion.objects.create(usuario=self.user, ancho_tablero=122,
              alto_tablero=244, piezas='P,20,30,1', num_tableros=1)
        data = dict(cliente=client.pk, optimizaciones=[opt.pk], precio_tablero=-1,
                    mano_obra=0, fecha_validez='2030-01-01', estado='borrador', nombre_cliente_nuevo='Otro')
        form = PresupuestoForm(data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('precio_tablero', form.errors)
        self.assertIn('nombre_cliente_nuevo', form.errors)

    def test_comparison_does_not_fill_missing_results(self):
        opts = [Optimizacion.objects.create(usuario=self.user, ancho_tablero=122,
                alto_tablero=244, piezas='P,20,30,1', num_tableros=n) for n in (0, 1)]
        response = self.client.get(reverse('cutless:comparar_optimizaciones'), {'opt1': opts[0].pk, 'opt2': opts[1].pk})
        self.assertEqual(response.status_code, 302)
        opts[0].refresh_from_db()
        self.assertEqual(opts[0].num_tableros, 0)

    def test_costs_invalid_date_does_not_show_unfiltered_records(self):
        Optimizacion.objects.create(usuario=self.user, ancho_tablero=122,
            alto_tablero=244, piezas='P,20,30,1', num_tableros=1, precio_tablero=100)
        for fechas in ({'fecha_desde': 'incorrecta'}, {'fecha_desde': '2030-02-02', 'fecha_hasta': '2030-01-01'}):
            response = self.client.get(reverse('cutless:historial_costos'), fechas)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.context['total_optimizaciones'], 0)

    def test_template_library_does_not_label_cm_as_meters(self):
        Plantilla.objects.create(usuario=self.user, nombre='En metros',
            ancho_tablero=122, alto_tablero=244, unidad_medida='m', piezas='P,0.2,0.3,1')
        response = self.client.get(reverse('cutless:lista_plantillas'))
        self.assertContains(response, '122,00 × 244,00 cm')

    def test_rut_se_normaliza_sin_puntos_y_con_guion(self):
        for entrada, esperado in [('12.345.678-9', '12345678-9'), ('123456789', '12345678-9'), ('12345678-k', '12345678-K'), ('', '')]:
            form = ClienteForm({'nombre': 'Cliente', 'rut': entrada}, user=self.user)
            self.assertTrue(form.is_valid(), form.errors)
            self.assertEqual(form.cleaned_data['rut'], esperado)
        for entrada in ('123--4', 'abc-k', '1234567890-1'):
            form = ClienteForm({'nombre': 'Cliente', 'rut': entrada}, user=self.user)
            self.assertFalse(form.is_valid())
            self.assertIn('rut', form.errors)

    def test_project_pagination_preserves_selection_without_assigning_early(self):
        project = Proyecto.objects.create(usuario=self.user, nombre='Paginado')
        opts = [Optimizacion.objects.create(usuario=self.user, nombre=f'Plan {n}',
            ancho_tablero=122, alto_tablero=244, piezas='P,20,30,1', num_tableros=1) for n in range(10)]
        url = reverse('cutless:agregar_optimizaciones_proyecto', args=[project.pk])
        first = self.client.get(url)
        self.assertEqual(len(first.context['optimizaciones_disponibles']), 8)
        self.assertEqual(first.context['pagina'].paginator.count, 10)
        selected = first.context['optimizaciones_disponibles'][0]
        second = self.client.post(url, {'operacion': 'siguiente', 'pagina': 1, 'optimizaciones': [selected.pk]})
        self.assertEqual(second.context['pagina'].number, 2)
        self.assertIn(selected.pk, second.context['seleccionadas_ocultas'])
        self.assertEqual(Optimizacion.objects.filter(proyecto=project).count(), 0)
        another = second.context['optimizaciones_disponibles'][0]
        self.client.post(url, {'operacion': 'agregar', 'optimizaciones': [selected.pk, another.pk]})
        self.assertEqual(set(project.optimizacion_set.values_list('pk', flat=True)), {selected.pk, another.pk})

    def test_project_search_keeps_selection_and_only_shows_eligible_plans(self):
        project = Proyecto.objects.create(usuario=self.user, nombre='Búsqueda')
        selected = Optimizacion.objects.create(usuario=self.user, nombre='Mesa',
            ancho_tablero=122, alto_tablero=244, piezas='P,20,30,1', num_tableros=1)
        url = reverse('cutless:agregar_optimizaciones_proyecto', args=[project.pk])
        response = self.client.post(url, {'operacion': 'buscar', 'busqueda': 'sin coincidencias',
                                         'optimizaciones': [selected.pk]})
        self.assertEqual(response.context['pagina'].paginator.count, 0)
        self.assertIn(selected.pk, response.context['seleccionadas_ocultas'])
        response = self.client.post(url, {'operacion': 'buscar', 'busqueda': selected.etiqueta})
        self.assertEqual([o.pk for o in response.context['optimizaciones_disponibles']], [selected.pk])

    def test_budget_invalid_post_preserves_date_and_multiple_plan_selection(self):
        opts = [Optimizacion.objects.create(usuario=self.user, nombre=f'Plan {n}',
                ancho_tablero=122, alto_tablero=244, piezas='P,20,30,1', num_tableros=1) for n in range(8)]
        response = self.client.post(reverse('cutless:crear_presupuesto'), {
            'optimizaciones': [opts[0].pk, opts[7].pk], 'precio_tablero': '-1',
            'mano_obra': '200', 'fecha_validez': '2030-12-20', 'estado': 'borrador', 'notas': 'Conservar nota'})
        self.assertEqual(response.status_code, 200)
        selected = {item['optimizacion'].pk for item in response.context['optimizaciones_info'] if item['seleccionada']}
        self.assertEqual(selected, {opts[0].pk, opts[7].pk})
        self.assertContains(response, 'value="2030-12-20"')
        self.assertContains(response, 'Conservar nota')
        self.assertContains(response, 'budget-plan-selector')

    def test_budget_edit_uses_same_selector_and_keeps_initial_selection(self):
        from cutless.models import Presupuesto
        budget = Presupuesto.objects.create(usuario=self.user, numero='SELECTOR', precio_tablero=100,
                    costo_total=100, fecha_validez=date(2030, 12, 20))
        opt = Optimizacion.objects.create(usuario=self.user, ancho_tablero=122,
                    alto_tablero=244, piezas='P,20,30,1', num_tableros=1)
        budget.optimizaciones.add(opt)
        response = self.client.get(reverse('cutless:editar_presupuesto', args=[budget.pk]))
        self.assertContains(response, 'value="2030-12-20"')
        self.assertTrue(response.context['optimizaciones_info'][0]['seleccionada'])
        self.assertContains(response, 'budget-plan-selector')
