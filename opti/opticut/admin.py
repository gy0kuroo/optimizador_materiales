from django.contrib import admin
from .models import Optimizacion

@admin.register(Optimizacion)
class OptimizacionAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'fecha', 'ancho_tablero', 'alto_tablero', 'aprovechamiento_total')
    search_fields = ('usuario__username',)
    ordering = ('-fecha',)
