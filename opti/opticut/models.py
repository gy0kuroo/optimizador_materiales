from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal

class Material(models.Model):
    """
    Modelo para gestionar tipos de tableros/materiales disponibles.
    Permite crear catálogo de materiales con precios.
    """
    UNIDADES_CHOICES = [
        ('cm', 'Centímetros (cm)'),
        ('m', 'Metros (m)'),
        ('in', 'Pulgadas (in)'),
        ('ft', 'Pies (ft)'),
    ]
    
    usuario = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        help_text="Usuario propietario. Null para materiales predefinidos del sistema."
    )
    nombre = models.CharField(max_length=100, help_text="Nombre del material (ej: MDF 18mm, Contrachapado)")
    ancho = models.FloatField(help_text="Ancho del tablero en cm")
    alto = models.FloatField(help_text="Alto del tablero en cm")
    unidad_medida = models.CharField(
        max_length=2, 
        choices=UNIDADES_CHOICES, 
        default='cm',
        help_text="Unidad de medida para mostrar"
    )
    precio = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Precio por tablero (opcional)"
    )
    es_predefinido = models.BooleanField(
        default=False,
        help_text="Si es True, es un material del sistema (no se puede eliminar)"
    )
    descripcion = models.TextField(blank=True, help_text="Descripción adicional del material")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Material"
        verbose_name_plural = "Materiales"
        ordering = ['-es_predefinido', 'nombre']
    
    def __str__(self):
        return f"{self.nombre} ({self.ancho}×{self.alto} {self.get_unidad_medida_display()})"
    
    def get_area(self):
        """Retorna el área del tablero en cm²"""
        return self.ancho * self.alto

class Optimizacion(models.Model):
    UNIDADES_CHOICES = [
        ('cm', 'Centímetros (cm)'),
        ('m', 'Metros (m)'),
        ('in', 'Pulgadas (in)'),
        ('ft', 'Pies (ft)'),
    ]
    
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    ancho_tablero = models.FloatField()  # Siempre guardado en cm (permite decimales)
    alto_tablero = models.FloatField()  # Siempre guardado en cm (permite decimales)
    unidad_medida = models.CharField(max_length=2, choices=UNIDADES_CHOICES, default='cm', 
                                     help_text="Unidad de medida usada por el usuario")
    piezas = models.TextField(help_text="Listado de piezas en formato ancho,alto,cantidad")
    imagen = models.ImageField(upload_to='optimizaciones/', null=True, blank=True)
    pdf = models.FileField(upload_to='pdfs/', null=True, blank=True)
    aprovechamiento_total = models.FloatField(default=0)
    # Campo legado para evitar errores de integridad en la BD
    favorito = models.BooleanField(default=False)
    # Nuevos campos para rotación y margen de corte
    permitir_rotacion = models.BooleanField(default=True, help_text="Permitir rotación automática de piezas 90°")
    margen_corte = models.FloatField(default=0.3, help_text="Margen de corte (kerf) en cm (guardado internamente). El valor se ingresa en mm.")
    
    # Campos para sistema de costos
    material = models.ForeignKey(
        Material, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text="Material/tablero utilizado (opcional)"
    )
    precio_tablero = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Precio por tablero usado en esta optimización"
    )
    mano_obra = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal('0.00'),
        help_text="Costo de mano de obra (opcional)"
    )
    num_tableros = models.IntegerField(
        default=0,
        help_text="Número de tableros utilizados (calculado automáticamente)"
    )

    def __str__(self):
        return f"Optimización de {self.usuario.username} ({self.fecha.strftime('%d/%m/%Y %H:%M')})"
    
    def calcular_costo_total(self):
        """
        Calcula el costo total de la optimización.
        Fórmula: (num_tableros × precio_tablero) + mano_obra
        """
        if self.precio_tablero is None:
            return None
        
        costo_material = Decimal(str(self.num_tableros)) * self.precio_tablero
        costo_total = costo_material + self.mano_obra
        return costo_total
    
    def get_costo_total(self):
        """Retorna el costo total formateado o None"""
        costo = self.calcular_costo_total()
        if costo is None:
            return None
        return costo
    
    # Campos para asociación con cliente y proyecto (Fase 2)
    cliente = models.ForeignKey(
        'Cliente',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Cliente asociado a esta optimización (opcional)"
    )
    proyecto = models.ForeignKey(
        'Proyecto',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Proyecto al que pertenece esta optimización (opcional)"
    )


class Cliente(models.Model):
    """
    Modelo para gestionar clientes del usuario.
    """
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, help_text="Usuario propietario del cliente")
    nombre = models.CharField(max_length=200, help_text="Nombre completo o razón social")
    rut = models.CharField(max_length=20, blank=True, help_text="RUT o identificación fiscal")
    email = models.EmailField(blank=True, help_text="Correo electrónico")
    telefono = models.CharField(max_length=20, blank=True, help_text="Teléfono de contacto")
    direccion = models.TextField(blank=True, help_text="Dirección completa")
    notas = models.TextField(blank=True, help_text="Notas adicionales sobre el cliente")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ['nombre']
        unique_together = [['usuario', 'nombre']]  # Un usuario no puede tener dos clientes con el mismo nombre
    
    def __str__(self):
        return self.nombre
    
    def get_total_optimizaciones(self):
        """Retorna el número total de optimizaciones para este cliente"""
        return self.optimizacion_set.count()
    
    def get_total_costo(self):
        """Retorna el costo total de todas las optimizaciones del cliente"""
        optimizaciones = self.optimizacion_set.all()
        total = Decimal('0.00')
        for opt in optimizaciones:
            costo = opt.get_costo_total()
            if costo:
                total += costo
        return total


class Proyecto(models.Model):
    """
    Modelo para agrupar múltiples optimizaciones en un proyecto.
    """
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, help_text="Usuario propietario del proyecto")
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Cliente asociado al proyecto (opcional)"
    )
    nombre = models.CharField(max_length=200, help_text="Nombre del proyecto")
    descripcion = models.TextField(blank=True, help_text="Descripción del proyecto")
    fecha_inicio = models.DateField(null=True, blank=True, help_text="Fecha de inicio del proyecto")
    fecha_fin = models.DateField(null=True, blank=True, help_text="Fecha de finalización estimada")
    estado = models.CharField(
        max_length=20,
        choices=[
            ('planificacion', 'Planificación'),
            ('en_proceso', 'En Proceso'),
            ('completado', 'Completado'),
            ('cancelado', 'Cancelado'),
        ],
        default='planificacion',
        help_text="Estado actual del proyecto"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Proyecto"
        verbose_name_plural = "Proyectos"
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return self.nombre
    
    def get_total_optimizaciones(self):
        """Retorna el número total de optimizaciones en el proyecto"""
        return self.optimizacion_set.count()
    
    def get_total_costo(self):
        """Retorna el costo total del proyecto"""
        optimizaciones = self.optimizacion_set.all()
        total = Decimal('0.00')
        for opt in optimizaciones:
            costo = opt.get_costo_total()
            if costo:
                total += costo
        return total


class Presupuesto(models.Model):
    """
    Modelo para generar presupuestos/cotizaciones profesionales.
    """
    ESTADOS_CHOICES = [
        ('borrador', 'Borrador'),
        ('enviado', 'Enviado'),
        ('aceptado', 'Aceptado'),
        ('rechazado', 'Rechazado'),
        ('vencido', 'Vencido'),
    ]
    
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        help_text="Usuario propietario del presupuesto"
    )
    proyecto = models.ForeignKey(
        Proyecto,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Proyecto asociado (opcional)"
    )
    optimizaciones = models.ManyToManyField(
        Optimizacion,
        related_name='presupuestos',
        help_text="Optimizaciones asociadas al presupuesto"
    )
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Cliente al que se envía el presupuesto"
    )
    numero = models.CharField(
        max_length=50,
        unique=True,
        help_text="Número único del presupuesto (ej: PRE-2025-001)"
    )
    precio_tablero = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Precio por tablero usado en el presupuesto"
    )
    mano_obra = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Costo de mano de obra"
    )
    costo_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Costo total del presupuesto"
    )
    fecha_validez = models.DateField(help_text="Fecha hasta la cual el presupuesto es válido")
    estado = models.CharField(
        max_length=20,
        choices=ESTADOS_CHOICES,
        default='borrador',
        help_text="Estado del presupuesto"
    )
    notas = models.TextField(blank=True, help_text="Notas adicionales para el cliente")
    pdf = models.FileField(upload_to='presupuestos/', null=True, blank=True, help_text="PDF generado del presupuesto")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Presupuesto"
        verbose_name_plural = "Presupuestos"
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"Presupuesto {self.numero} - {self.cliente.nombre if self.cliente else 'Sin cliente'}"
    
    def esta_vencido(self):
        """Verifica si el presupuesto está vencido"""
        from django.utils import timezone
        return timezone.now().date() > self.fecha_validez
    
    def get_total_optimizaciones(self):
        """Retorna el número total de optimizaciones en el presupuesto"""
        return self.optimizaciones.count()
    
    def calcular_costo_total_multiple(self):
        """
        Calcula el costo total del presupuesto considerando todas las optimizaciones.
        Fórmula: Suma de (tableros × precio_tablero) para cada optimización + mano_obra total
        """
        total = Decimal('0.00')
        # Sumar costo de tableros de todas las optimizaciones
        for optimizacion in self.optimizaciones.all():
            num_tableros = optimizacion.num_tableros or 0
            costo_material = self.precio_tablero * Decimal(str(num_tableros))
            total += costo_material
        # Agregar mano de obra una sola vez (no por optimización)
        total += self.mano_obra
        return total
    
    def get_total_tableros(self):
        """Retorna el total de tableros de todas las optimizaciones"""
        return sum(opt.num_tableros or 0 for opt in self.optimizaciones.all())
    
    @staticmethod
    def generar_numero_presupuesto(usuario=None):
        """
        Genera un número único de presupuesto en formato PRE-YYYY-NNNN
        Ejemplo: PRE-2025-0001
        Si se proporciona un usuario, solo busca entre sus presupuestos.
        """
        from django.utils import timezone
        año_actual = timezone.now().year
        
        # Buscar el último presupuesto del año actual
        query = Presupuesto.objects.filter(
            numero__startswith=f'PRE-{año_actual}-'
        )
        if usuario:
            query = query.filter(usuario=usuario)
        ultimo_presupuesto = query.order_by('-numero').first()
        
        if ultimo_presupuesto:
            # Extraer el número secuencial
            try:
                numero_secuencial = int(ultimo_presupuesto.numero.split('-')[-1])
                nuevo_numero = numero_secuencial + 1
            except (ValueError, IndexError):
                nuevo_numero = 1
        else:
            nuevo_numero = 1
        
        # Formatear con ceros a la izquierda (4 dígitos)
        return f'PRE-{año_actual}-{nuevo_numero:04d}'


class Plantilla(models.Model):
    """
    Modelo para guardar optimizaciones como plantillas reutilizables.
    Fase 4: Plantillas Avanzadas
    """
    CATEGORIAS_CHOICES = [
        ('cocina', 'Cocina'),
        ('muebles', 'Muebles'),
        ('puertas', 'Puertas'),
        ('ventanas', 'Ventanas'),
        ('estantes', 'Estantes'),
        ('otros', 'Otros'),
    ]
    
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Usuario propietario. Null para plantillas predefinidas del sistema."
    )
    nombre = models.CharField(max_length=200, help_text="Nombre de la plantilla")
    descripcion = models.TextField(blank=True, help_text="Descripción de la plantilla")
    categoria = models.CharField(
        max_length=20,
        choices=CATEGORIAS_CHOICES,
        default='otros',
        help_text="Categoría de la plantilla"
    )
    ancho_tablero = models.FloatField(help_text="Ancho del tablero en cm")
    alto_tablero = models.FloatField(help_text="Alto del tablero en cm")
    unidad_medida = models.CharField(
        max_length=2,
        choices=Material.UNIDADES_CHOICES,
        default='cm',
        help_text="Unidad de medida"
    )
    piezas = models.TextField(help_text="Listado de piezas en formato nombre,ancho,alto,cantidad")
    permitir_rotacion = models.BooleanField(default=True, help_text="Permitir rotación automática")
    margen_corte = models.FloatField(default=0.3, help_text="Margen de corte en cm")
    es_predefinida = models.BooleanField(
        default=False,
        help_text="Si es True, es una plantilla del sistema (no se puede eliminar)"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Plantilla"
        verbose_name_plural = "Plantillas"
        ordering = ['-es_predefinida', 'categoria', 'nombre']
        unique_together = [['usuario', 'nombre']]  # Un usuario no puede tener dos plantillas con el mismo nombre
    
    def __str__(self):
        return self.nombre
    
    def get_piezas_list(self):
        """Retorna la lista de piezas parseada"""
        piezas_list = []
        for linea in self.piezas.splitlines():
            if linea.strip():
                partes = linea.split(',')
                if len(partes) == 4:
                    piezas_list.append({
                        'nombre': partes[0].strip(),
                        'ancho': float(partes[1].strip()),
                        'alto': float(partes[2].strip()),
                        'cantidad': int(partes[3].strip())
                    })
        return piezas_list
