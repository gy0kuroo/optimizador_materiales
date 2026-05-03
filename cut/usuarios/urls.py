from django.urls import path
from . import views

app_name = 'usuarios'

urlpatterns = [
    path('registro/', views.registro, name='registro'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('perfil/', views.perfil, name='perfil'),
    path('configuracion-sistema/', views.configuracion_sistema, name='configuracion_sistema'),
    path('completar-tutorial/', views.completar_tutorial, name='completar_tutorial'),
    path('recuperar-password/', views.recuperar_password, name='recuperar_password'),
    path('reset-password/<uidb64>/<token>/', views.reset_password_confirm, name='reset_password_confirm'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('eliminar-usuario/<int:pk>/', views.eliminar_usuario, name='eliminar_usuario'),
    path('actualizar-rol/<int:pk>/', views.actualizar_rol, name='actualizar_rol'),
    path('editar-usuario/<int:pk>/', views.editar_usuario, name='editar_usuario'),
]
