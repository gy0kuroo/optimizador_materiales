from django.urls import path
from . import views

app_name = "cutless"

urlpatterns = [
    # Páginas principales
    path("", views.index, name="index"),
    path('historial/', views.historial, name='historial'),
    path('estadisticas/', views.estadisticas, name='estadisticas'),
    path('estadisticas/exportar-excel-desperdicio/', views.exportar_excel_desperdicio, name='exportar_excel_desperdicio'),
    path('estadisticas/exportar-pdf-desperdicio/', views.exportar_pdf_desperdicio, name='exportar_pdf_desperdicio'),
    path('resultado/<int:pk>/', views.resultado_view, name='resultado'),
    
    # Acciones sobre optimizaciones
    path('editar/<int:pk>/', views.editar_optimizacion, name='editar_optimizacion'),
    path('duplicar/<int:pk>/', views.duplicar_optimizacion, name='duplicar_optimizacion'),
    path('toggle-favorito/<int:pk>/', views.toggle_favorito, name='toggle_favorito'),
    path('borrar/<int:pk>/', views.borrar_optimizacion, name='borrar_optimizacion'),
    path('borrar-historial/', views.borrar_historial, name='borrar_historial'),
    path('borrar-seleccion/', views.borrar_seleccion, name='borrar_seleccion'),
    
    # Descargas
    path('descargar-pdf/<int:pk>/', views.descargar_pdf, name='descargar_pdf'),
    path('descargar-excel/<int:pk>/', views.descargar_excel, name='descargar_excel'),
    path('descargar-png/<int:pk>/', views.descargar_png, name='descargar_png'),
    path('descargar-png/<int:pk>/<int:tablero_num>/', views.descargar_png, name='descargar_png_tablero'),
    path('imprimir-plan-corte/<int:pk>/', views.imprimir_plan_corte, name='imprimir_plan_corte'),
    
    # Utilidades
    path('calcular-tiempo/<int:pk>/', views.calcular_tiempo_corte, name='calcular_tiempo_corte'),
    
    # API
    path('api/tableros/<int:pk>/', views.api_tableros_optimizacion, name='api_tableros'),
    
    # Gestión de materiales
    path('materiales/', views.lista_materiales, name='lista_materiales'),
    path('materiales/crear/', views.crear_material, name='crear_material'),
    path('materiales/editar/<int:pk>/', views.editar_material, name='editar_material'),
    path('materiales/eliminar/<int:pk>/', views.eliminar_material, name='eliminar_material'),
    
    # Gestión de clientes (Fase 2)
    path('clientes/', views.lista_clientes, name='lista_clientes'),
    path('clientes/crear/', views.crear_cliente, name='crear_cliente'),
    path('clientes/editar/<int:pk>/', views.editar_cliente, name='editar_cliente'),
    path('clientes/eliminar/<int:pk>/', views.eliminar_cliente, name='eliminar_cliente'),
    path('clientes/historial/<int:pk>/', views.historial_cliente, name='historial_cliente'),
    
    # Gestión de presupuestos (Fase 2)
    path('presupuestos/', views.lista_presupuestos, name='lista_presupuestos'),
    path('presupuestos/crear/', views.crear_presupuesto, name='crear_presupuesto'),
    path('presupuestos/editar/<int:pk>/', views.editar_presupuesto, name='editar_presupuesto'),
    path('presupuestos/<int:pk>/', views.detalle_presupuesto, name='detalle_presupuesto'),
    path('presupuestos/<int:pk>/pdf/', views.generar_pdf_presupuesto, name='generar_pdf_presupuesto'),
    path('presupuestos/<int:pk>/agregar-optimizaciones/', views.agregar_optimizaciones_presupuesto, name='agregar_optimizaciones_presupuesto'),
    
    # Historial de costos (Fase 2)
    path('historial-costos/', views.historial_costos, name='historial_costos'),
    
    # Gestión de proyectos (Fase 3)
    path('proyectos/', views.lista_proyectos, name='lista_proyectos'),
    path('proyectos/crear/', views.crear_proyecto, name='crear_proyecto'),
    path('proyectos/<int:pk>/', views.detalle_proyecto, name='detalle_proyecto'),
    path('proyectos/editar/<int:pk>/', views.editar_proyecto, name='editar_proyecto'),
    path('proyectos/eliminar/<int:pk>/', views.eliminar_proyecto, name='eliminar_proyecto'),
    path('proyectos/<int:pk>/agregar-optimizaciones/', views.agregar_optimizaciones_proyecto, name='agregar_optimizaciones_proyecto'),
    
    # Comparación de optimizaciones (Fase 3)
    path('comparar/', views.comparar_optimizaciones, name='comparar_optimizaciones'),
    
    # Gestión de plantillas (Fase 4)
    path('plantillas/', views.lista_plantillas, name='lista_plantillas'),
    path('plantillas/crear/', views.crear_plantilla, name='crear_plantilla'),
    path('plantillas/editar/<int:pk>/', views.editar_plantilla, name='editar_plantilla'),
    path('plantillas/eliminar/<int:pk>/', views.eliminar_plantilla, name='eliminar_plantilla'),
    path('plantillas/usar/<int:pk>/', views.usar_plantilla, name='usar_plantilla'),
]
