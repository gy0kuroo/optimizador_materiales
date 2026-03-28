from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal

class PerfilUsuario(models.Model):
    """
    Modelo para almacenar información adicional del usuario y sus preferencias
    """
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    
    # ===== CONFIGURACIÓN DE SESIÓN Y APARIENCIA =====
    # Timeout de sesión en minutos. None = usar configuración por defecto del sistema
    timeout_sesion = models.IntegerField(
        null=True, 
        blank=True, 
        help_text="Tiempo de inactividad antes de cerrar sesión (en minutos). Déjalo vacío para usar el valor por defecto (30 min). 0 para desactivar."
    )

    # Rol de usuario dentro de la aplicación
    ROL_CHOICES = [
        ('usuario', 'Usuario'),
        ('admin', 'Administrador'),
    ]
    rol = models.CharField(
        max_length=20,
        choices=ROL_CHOICES,
        default='usuario',
        help_text="Rol del usuario en el sistema"
    )
    # Tema preferido (opcional, para futuras mejoras)
    tema_preferido = models.CharField(
        max_length=10, 
        choices=[('light', 'Claro'), ('dark', 'Oscuro'), ('auto', 'Automático')],
        default='auto',
        help_text="Tema de color preferido"
    )
    tamanio_fuente = models.CharField(
        max_length=10,
        choices=[
            ('small', 'Pequeño'),
            ('normal', 'Normal'),
            ('large', 'Grande'),
            ('xlarge', 'Extra Grande')
        ],
        default='normal',
        help_text="Tamaño de fuente preferido para facilitar la lectura",
    )
    tutorial_completado = models.BooleanField(
        default=False,
        help_text="Indica si el usuario ha completado el tutorial inicial"
    )
    
    # ===== CONFIGURACIÓN DE OPTIMIZACIÓN (VALORES POR DEFECTO) =====
    # Unidad de medida predeterminada
    unidad_medida_predeterminada = models.CharField(
        max_length=10,
        choices=[
            ('cm', 'Centímetros (cm)'),
            ('m', 'Metros (m)'),
            ('mm', 'Milímetros (mm)'),
            ('in', 'Pulgadas (in)'),
            ('ft', 'Pies (ft)'),
        ],
        default='cm',
        help_text="Unidad de medida que se usará por defecto en nuevas optimizaciones"
    )
    
    # Algoritmo de optimización predeterminado
    algoritmo_predeterminado = models.CharField(
        max_length=20,
        choices=[
            ('ffd', 'First Fit Decreasing (FFD)'),
            ('best_fit', 'Best Fit'),
            ('first_fit', 'First Fit'),
        ],
        default='ffd',
        help_text="Algoritmo de optimización que se usará por defecto"
    )
    
    # Margen de corte predeterminado (en cm)
    margen_corte_predeterminado = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.3'),
        help_text="Margen de corte predeterminado en centímetros"
    )
    
    # Rotación automática predeterminada
    rotacion_automatica_predeterminada = models.BooleanField(
        default=True,
        help_text="Permitir rotación automática de piezas por defecto"
    )
    
    # Material predeterminado (opcional)
    material_predeterminado = models.ForeignKey(
        'opticut.Material',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='usuarios_con_material_predeterminado',
        help_text="Material que se seleccionará por defecto en nuevas optimizaciones"
    )
    
    # Precio de tablero predeterminado
    precio_tablero_predeterminado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Precio por tablero que se usará por defecto (opcional)"
    )
    
    # Mano de obra predeterminada
    mano_obra_predeterminada = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        default=Decimal('0.00'),
        help_text="Costo de mano de obra que se usará por defecto (opcional)"
    )
    
    # ===== CONFIGURACIÓN DE NOTIFICACIONES =====
    # Activar/desactivar notificaciones por email
    notificaciones_email = models.BooleanField(
        default=False,
        help_text="Recibir notificaciones por correo electrónico"
    )
    
    # Activar/desactivar notificaciones en pantalla
    notificaciones_pantalla = models.BooleanField(
        default=True,
        help_text="Mostrar notificaciones en pantalla"
    )
    
    # Email para notificaciones (opcional, por defecto el email del usuario)
    email_notificaciones = models.EmailField(
        null=True,
        blank=True,
        help_text="Email para recibir notificaciones (opcional, por defecto se usa el email del usuario)"
    )
    
    # Notificar cuando se completa una optimización
    notificar_optimizacion_completada = models.BooleanField(
        default=True,
        help_text="Notificar cuando se completa una optimización"
    )
    
    # Notificar cuando se crea un presupuesto
    notificar_presupuesto_creado = models.BooleanField(
        default=True,
        help_text="Notificar cuando se crea un presupuesto"
    )
    
    # Notificar cuando se crea un proyecto
    notificar_proyecto_creado = models.BooleanField(
        default=True,
        help_text="Notificar cuando se crea un proyecto"
    )
    
    # Notificar cuando hay errores en la optimización
    notificar_errores = models.BooleanField(
        default=True,
        help_text="Notificar cuando hay errores en la optimización"
    )
    
    # ===== PERMISOS Y FUNCIONALIDADES PERSONALIZADAS =====
    # Funcionalidades activadas (por defecto todas activas)
    puede_crear_plantillas = models.BooleanField(
        default=True,
        help_text="Permitir crear y editar plantillas"
    )
    
    puede_comparar_optimizaciones = models.BooleanField(
        default=True,
        help_text="Permitir acceso a herramienta de comparación"
    )
    
    puede_crear_clientes = models.BooleanField(
        default=True,
        help_text="Permitir crear y editar clientes"
    )
    
    puede_crear_proyectos = models.BooleanField(
        default=True,
        help_text="Permitir crear y editar proyectos"
    )
    
    puede_crear_presupuestos = models.BooleanField(
        default=True,
        help_text="Permitir crear y editar presupuestos"
    )
    
    puede_crear_materiales = models.BooleanField(
        default=True,
        help_text="Permitir crear y editar materiales"
    )
    
    puede_ver_estadisticas = models.BooleanField(
        default=True,
        help_text="Permitir acceso a estadísticas"
    )
    
    puede_ver_historial_costos = models.BooleanField(
        default=True,
        help_text="Permitir acceso a historial de costos"
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
