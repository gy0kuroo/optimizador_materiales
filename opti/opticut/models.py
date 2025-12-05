from django.db import models
from django.contrib.auth.models import User

class Optimizacion(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    ancho_tablero = models.IntegerField()
    alto_tablero = models.IntegerField()
    piezas = models.TextField(help_text="Listado de piezas en formato ancho,alto,cantidad")
    imagen = models.ImageField(upload_to='optimizaciones/', null=True, blank=True)
    pdf = models.FileField(upload_to='optimizaciones_pdfs/', null=True, blank=True)
    aprovechamiento_total = models.FloatField(default=0)
    # Campo legado para evitar errores de integridad en la BD
    favorito = models.BooleanField(default=False)

    def __str__(self):
        return f"Optimización de {self.usuario.username} ({self.fecha.strftime('%d/%m/%Y %H:%M')})"
