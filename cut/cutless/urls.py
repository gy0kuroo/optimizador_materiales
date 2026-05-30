from django.contrib.auth.decorators import login_required
from django.urls import path
from . import views
from .views.common import requiere_permiso

app_name = "cutless"


def auth(view):
    """Vista accesible para cualquier usuario autenticado."""
    return login_required(view)


def auth_perm(permiso, view):
    """Vista que exige login y un permiso del perfil (puede_*)."""
    return login_required(requiere_permiso(permiso)(view))


urlpatterns = [
    # Páginas principales (optimizador e historial: acceso base)
    path("", auth(views.index), name="index"),
    path('historial/', auth(views.historial), name='historial'),
    path('resultado/<int:pk>/', auth(views.resultado_view), name='resultado'),

    # Estadísticas y exportaciones de desperdicio
    path('estadisticas/', auth_perm('puede_ver_estadisticas', views.estadisticas), name='estadisticas'),
    path(
        'estadisticas/exportar-excel-desperdicio/',
        auth_perm('puede_ver_estadisticas', views.exportar_excel_desperdicio),
        name='exportar_excel_desperdicio',
    ),
    path(
        'estadisticas/exportar-pdf-desperdicio/',
        auth_perm('puede_ver_estadisticas', views.exportar_pdf_desperdicio),
        name='exportar_pdf_desperdicio',
    ),

    # Acciones sobre optimizaciones (propias del usuario)
    path('editar/<int:pk>/', auth(views.editar_optimizacion), name='editar_optimizacion'),
    path('duplicar/<int:pk>/', auth(views.duplicar_optimizacion), name='duplicar_optimizacion'),
    path('toggle-favorito/<int:pk>/', auth(views.toggle_favorito), name='toggle_favorito'),
    path('borrar/<int:pk>/', auth(views.borrar_optimizacion), name='borrar_optimizacion'),
    path('borrar-historial/', auth(views.borrar_historial), name='borrar_historial'),
    path('borrar-seleccion/', auth(views.borrar_seleccion), name='borrar_seleccion'),

    # Descargas de optimizaciones propias
    path('descargar-pdf/<int:pk>/', auth(views.descargar_pdf), name='descargar_pdf'),
    path('descargar-excel/<int:pk>/', auth(views.descargar_excel), name='descargar_excel'),
    path('descargar-png/<int:pk>/', auth(views.descargar_png), name='descargar_png'),
    path('descargar-png/<int:pk>/<int:tablero_num>/', auth(views.descargar_png), name='descargar_png_tablero'),
    path('imprimir-plan-corte/<int:pk>/', auth(views.imprimir_plan_corte), name='imprimir_plan_corte'),

    # Utilidades
    path('calcular-tiempo/<int:pk>/', auth(views.calcular_tiempo_corte), name='calcular_tiempo_corte'),

    # API
    path('api/tableros/<int:pk>/', auth(views.api_tableros_optimizacion), name='api_tableros'),

    # Gestión de materiales
    path('materiales/', auth_perm('puede_crear_materiales', views.lista_materiales), name='lista_materiales'),
    path('materiales/crear/', auth_perm('puede_crear_materiales', views.crear_material), name='crear_material'),
    path('materiales/editar/<int:pk>/', auth_perm('puede_crear_materiales', views.editar_material), name='editar_material'),
    path('materiales/eliminar/<int:pk>/', auth_perm('puede_crear_materiales', views.eliminar_material), name='eliminar_material'),

    # Gestión de clientes
    path('clientes/', auth_perm('puede_crear_clientes', views.lista_clientes), name='lista_clientes'),
    path('clientes/crear/', auth_perm('puede_crear_clientes', views.crear_cliente), name='crear_cliente'),
    path('clientes/editar/<int:pk>/', auth_perm('puede_crear_clientes', views.editar_cliente), name='editar_cliente'),
    path('clientes/eliminar/<int:pk>/', auth_perm('puede_crear_clientes', views.eliminar_cliente), name='eliminar_cliente'),
    path('clientes/historial/<int:pk>/', auth_perm('puede_crear_clientes', views.historial_cliente), name='historial_cliente'),

    # Gestión de presupuestos
    path('presupuestos/', auth_perm('puede_crear_presupuestos', views.lista_presupuestos), name='lista_presupuestos'),
    path('presupuestos/crear/', auth_perm('puede_crear_presupuestos', views.crear_presupuesto), name='crear_presupuesto'),
    path('presupuestos/editar/<int:pk>/', auth_perm('puede_crear_presupuestos', views.editar_presupuesto), name='editar_presupuesto'),
    path('presupuestos/<int:pk>/', auth_perm('puede_crear_presupuestos', views.detalle_presupuesto), name='detalle_presupuesto'),
    path('presupuestos/<int:pk>/pdf/', auth_perm('puede_crear_presupuestos', views.generar_pdf_presupuesto), name='generar_pdf_presupuesto'),
    path(
        'presupuestos/<int:pk>/agregar-optimizaciones/',
        auth_perm('puede_crear_presupuestos', views.agregar_optimizaciones_presupuesto),
        name='agregar_optimizaciones_presupuesto',
    ),

    # Historial de costos
    path('historial-costos/', auth_perm('puede_ver_historial_costos', views.historial_costos), name='historial_costos'),

    # Gestión de proyectos
    path('proyectos/', auth_perm('puede_crear_proyectos', views.lista_proyectos), name='lista_proyectos'),
    path('proyectos/crear/', auth_perm('puede_crear_proyectos', views.crear_proyecto), name='crear_proyecto'),
    path('proyectos/<int:pk>/', auth_perm('puede_crear_proyectos', views.detalle_proyecto), name='detalle_proyecto'),
    path('proyectos/editar/<int:pk>/', auth_perm('puede_crear_proyectos', views.editar_proyecto), name='editar_proyecto'),
    path('proyectos/eliminar/<int:pk>/', auth_perm('puede_crear_proyectos', views.eliminar_proyecto), name='eliminar_proyecto'),
    path(
        'proyectos/<int:pk>/agregar-optimizaciones/',
        auth_perm('puede_crear_proyectos', views.agregar_optimizaciones_proyecto),
        name='agregar_optimizaciones_proyecto',
    ),

    # Comparación de optimizaciones
    path('comparar/', auth_perm('puede_comparar_optimizaciones', views.comparar_optimizaciones), name='comparar_optimizaciones'),

    # Gestión de plantillas
    path('plantillas/', auth_perm('puede_crear_plantillas', views.lista_plantillas), name='lista_plantillas'),
    path('plantillas/crear/', auth_perm('puede_crear_plantillas', views.crear_plantilla), name='crear_plantilla'),
    path('plantillas/editar/<int:pk>/', auth_perm('puede_crear_plantillas', views.editar_plantilla), name='editar_plantilla'),
    path('plantillas/eliminar/<int:pk>/', auth_perm('puede_crear_plantillas', views.eliminar_plantilla), name='eliminar_plantilla'),
    path('plantillas/usar/<int:pk>/', auth_perm('puede_crear_plantillas', views.usar_plantilla), name='usar_plantilla'),
]
