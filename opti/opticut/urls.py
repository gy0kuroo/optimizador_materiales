from django.urls import path
from . import views

app_name = "opticut"

urlpatterns = [
    path("", views.index, name="index"),
    path('mis-optimizaciones/', views.mis_optimizaciones, name='mis_optimizaciones'),
    path('estadisticas/', views.estadisticas, name='estadisticas'),
    path('borrar-historial/', views.borrar_historial, name='borrar_historial'),
    path('borrar/<int:pk>/', views.borrar_optimizacion, name='borrar_optimizacion'),
    path('descargar-pdf/<int:pk>/', views.descargar_pdf, name='descargar_pdf'),
    path('duplicar/<int:pk>/', views.duplicar_optimizacion, name='duplicar_optimizacion'),
    path('toggle-favorito/<int:pk>/', views.toggle_favorito, name='toggle_favorito'),
    path('calcular-tiempo/<int:pk>/', views.calcular_tiempo_corte, name='calcular_tiempo_corte'),
    path('descargar-png/<int:pk>/', views.descargar_png, name='descargar_png'),
    path('descargar-png/<int:pk>/<int:tablero_num>/', views.descargar_png, name='descargar_png_tablero'),
]
