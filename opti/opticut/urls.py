from django.urls import path
from . import views

app_name = "opticut"

urlpatterns = [
    # Páginas principales
    path("", views.index, name="index"),
    path('historial/', views.historial, name='historial'),
    path('estadisticas/', views.estadisticas, name='estadisticas'),
    
    # Acciones sobre optimizaciones
    path('editar/<int:pk>/', views.editar_optimizacion, name='editar_optimizacion'),
    path('duplicar/<int:pk>/', views.duplicar_optimizacion, name='duplicar_optimizacion'),
    path('toggle-favorito/<int:pk>/', views.toggle_favorito, name='toggle_favorito'),
    path('borrar/<int:pk>/', views.borrar_optimizacion, name='borrar_optimizacion'),
    path('borrar-historial/', views.borrar_historial, name='borrar_historial'),
    
    # Descargas
    path('descargar-pdf/<int:pk>/', views.descargar_pdf, name='descargar_pdf'),
    path('descargar-excel/<int:pk>/', views.descargar_excel, name='descargar_excel'),
    path('descargar-png/<int:pk>/', views.descargar_png, name='descargar_png'),
    path('descargar-png/<int:pk>/<int:tablero_num>/', views.descargar_png, name='descargar_png_tablero'),
    
    # Utilidades
    path('calcular-tiempo/<int:pk>/', views.calcular_tiempo_corte, name='calcular_tiempo_corte'),
]
