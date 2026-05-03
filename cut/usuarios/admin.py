from django.contrib import admin
from .models import PerfilUsuario

@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'timeout_sesion', 'tema_preferido', 'fecha_creacion')
    list_filter = ('tema_preferido', 'timeout_sesion')
    search_fields = ('usuario__username', 'usuario__email')
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')
