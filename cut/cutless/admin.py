from django.contrib import admin
from .models import Optimizacion, Material

@admin.register(Optimizacion)
class OptimizacionAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'fecha', 'ancho_tablero', 'alto_tablero', 'aprovechamiento_total', 'costo_total_display')
    search_fields = ('usuario__username',)
    ordering = ('-fecha',)
    list_filter = ('fecha', 'aprovechamiento_total')
    
    def costo_total_display(self, obj):
        costo = obj.get_costo_total()
        if costo:
            return f"${costo:,.0f}"
        return "-"
    costo_total_display.short_description = "Costo Total"

@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'ancho', 'alto', 'unidad_medida', 'precio', 'es_predefinido', 'usuario', 'fecha_creacion')
    search_fields = ('nombre', 'descripcion')
    list_filter = ('es_predefinido', 'unidad_medida', 'fecha_creacion')
    ordering = ('-es_predefinido', 'nombre')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Los usuarios normales solo ven sus materiales y los predefinidos
        return qs.filter(usuario=request.user) | qs.filter(es_predefinido=True)
