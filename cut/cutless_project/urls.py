"""
URL configuration para CutLess (cutless_project).

La aplicación vive bajo /cutless/.
"""
from django.contrib import admin
from django.urls import path
from django.urls import include
from django.shortcuts import redirect
from cutless.views.media import media_privada


def root_redirect(request):
    if request.user.is_authenticated:
        return redirect('cutless:index')
    return redirect('usuarios:login')


urlpatterns = [
    path('', root_redirect, name='root_redirect'),
    path('media/<path:archivo>', media_privada, name='media_privada'),
    path('admin/', admin.site.urls),
    path('usuarios/', include('usuarios.urls')),
    path('cutless/', include('cutless.urls')),
]



handler404 = 'cutless.views.handler404'
handler500 = 'cutless.views.handler500'
