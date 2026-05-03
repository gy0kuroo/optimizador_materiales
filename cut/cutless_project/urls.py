"""
URL configuration para CutLess (cutless_project).

La aplicación vive bajo /cutless/.
"""
from django.contrib import admin
from django.urls import path
from django.urls import include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect


def root_redirect(request):
    if request.user.is_authenticated:
        return redirect('cutless:index')
    return redirect('usuarios:login')


urlpatterns = [
    path('', root_redirect, name='root_redirect'),
    path('admin/', admin.site.urls),
    path('usuarios/', include('usuarios.urls')),
    path('cutless/', include('cutless.urls')),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = 'cutless.views.handler404'
handler500 = 'cutless.views.handler500'
