from django.urls import path
from . import views

app_name = "opticut"

urlpatterns = [
    path("", views.index, name="index"),
    path('mis-optimizaciones/', views.mis_optimizaciones, name='mis_optimizaciones'),
    path('borrar-historial/', views.borrar_historial, name='borrar_historial'),
    path('borrar/<int:pk>/', views.borrar_optimizacion, name='borrar_optimizacion'),
    path('descargar-pdf/<int:pk>/', views.descargar_pdf, name='descargar_pdf'),
    path('duplicar/<int:pk>/', views.duplicar_optimizacion, name='duplicar_optimizacion'),
]
