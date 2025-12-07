from django.db import models
from django.contrib.auth.models import User

class Optimizacion(models.Model):
    UNIDADES_CHOICES = [
        ('cm', 'Centímetros (cm)'),
        ('m', 'Metros (m)'),
        ('in', 'Pulgadas (in)'),
        ('ft', 'Pies (ft)'),
    ]
    
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    ancho_tablero = models.IntegerField()  # Siempre guardado en cm
    alto_tablero = models.IntegerField()  # Siempre guardado en cm
    unidad_medida = models.CharField(max_length=2, choices=UNIDADES_CHOICES, default='cm', 
                                     help_text="Unidad de medida usada por el usuario")
    piezas = models.TextField(help_text="Listado de piezas en formato ancho,alto,cantidad")
    imagen = models.ImageField(upload_to='optimizaciones/', null=True, blank=True)
    pdf = models.FileField(upload_to='pdfs/', null=True, blank=True)
    aprovechamiento_total = models.FloatField(default=0)
    # Campo legado para evitar errores de integridad en la BD
    favorito = models.BooleanField(default=False)

    def __str__(self):
        return f"Optimización de {self.usuario.username} ({self.fecha.strftime('%d/%m/%Y %H:%M')})"
