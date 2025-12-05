from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class PerfilUsuario(models.Model):
    """
    Modelo para almacenar información adicional del usuario y sus preferencias
    """
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    # Timeout de sesión en minutos. None = usar configuración por defecto del sistema
    timeout_sesion = models.IntegerField(
        null=True, 
        blank=True, 
        help_text="Tiempo de inactividad antes de cerrar sesión (en minutos). Déjalo vacío para usar el valor por defecto (30 min). 0 para desactivar."
    )
    # Tema preferido (opcional, para futuras mejoras)
    tema_preferido = models.CharField(
        max_length=10, 
        choices=[('light', 'Claro'), ('dark', 'Oscuro'), ('auto', 'Automático')],
        default='auto',
        help_text="Tema de color preferido"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Perfil de Usuario"
        verbose_name_plural = "Perfiles de Usuarios"

    def __str__(self):
        return f"Perfil de {self.usuario.username}"

    def get_timeout_segundos(self):
        """Retorna el timeout en segundos, o None si está desactivado"""
        if self.timeout_sesion is None:
            return 1800  # 30 minutos por defecto
        if self.timeout_sesion == 0:
            return None  # Desactivado
        return self.timeout_sesion * 60
    
    def get_timeout_segundos_str(self):
        """Retorna el timeout en segundos como string, o '0' si está desactivado"""
        if self.timeout_sesion is None:
            return '1800'  # 30 minutos por defecto
        if self.timeout_sesion == 0:
            return '0'  # Desactivado
        return str(self.timeout_sesion * 60)

@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    """Crea automáticamente un perfil cuando se crea un usuario"""
    if created:
        PerfilUsuario.objects.create(usuario=instance)
