from django import forms
from django.db import models
from django.db.models import Q
from .models import Material, Cliente, Presupuesto, Proyecto, Plantilla, Optimizacion

class TableroForm(forms.Form):
    UNIDADES_CHOICES = [
        ('cm', 'Centímetros (cm)'),
        ('m', 'Metros (m)'),
        ('mm', 'Milímetros (mm)'),
        ('in', 'Pulgadas (in)'),
        ('ft', 'Pies (ft)'),
    ]
    
    unidad_medida = forms.ChoiceField(
        label="Unidad de medida",
        choices=UNIDADES_CHOICES,
        initial='cm',
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'unidad_medida_selector',
            'onchange': 'actualizarLabelsUnidad()'
        }),
        help_text="Selecciona la unidad de medida"
    )
    
    ancho = forms.FloatField(
        label="Ancho del tablero",
        min_value=0.1,
        max_value=1000,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 122',
            'id': 'ancho_tablero',
            'step': '0.01'
        }),
        help_text="Ingresa el ancho del tablero"
    )
    
    alto = forms.FloatField(
        label="Alto del tablero",
        min_value=0.1,
        max_value=1000,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 244',
            'id': 'alto_tablero',
            'step': '0.01'
        }),
        help_text="Ingresa el alto del tablero"
    )
    
    permitir_rotacion = forms.BooleanField(
        label="Permitir rotación automática",
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'permitir_rotacion'
        }),
        help_text="El sistema intentará rotar piezas 90° si mejora el aprovechamiento"
    )
    
    margen_corte = forms.FloatField(
        label="Margen de corte (kerf)",
        min_value=0,
        max_value=10,  # Máximo 10 mm
        initial=3,  # 3 mm es un valor típico
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '3',
            'step': '0.1',
            'id': 'margen_corte'
        }),
        help_text="Grosor de la hoja de sierra en milímetros (típicamente 2-4 mm)"
    )
    
    # Campos para sistema de costos
    material = forms.ModelChoiceField(
        label="Material/Tablero",
        queryset=Material.objects.none(),  # Se actualizará en __init__
        required=False,
        empty_label="Seleccionar material (opcional)",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'material_select'
        }),
        help_text="Selecciona un material de tu biblioteca para calcular costos automáticamente"
    )
    
    precio_tablero = forms.DecimalField(
        label="Precio por tablero",
        max_digits=10,
        decimal_places=2,
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0',
            'step': '0.01',
            'id': 'precio_tablero'
        }),
        help_text="Precio en pesos chilenos (se llena automáticamente si seleccionas un material)"
    )
    
    mano_obra = forms.DecimalField(
        label="Mano de obra",
        max_digits=10,
        decimal_places=2,
        required=False,
        min_value=0,
        initial=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0',
            'step': '0.01',
            'id': 'mano_obra'
        }),
        help_text="Costo adicional de mano de obra (opcional)"
    )
    
    # Campo para asociar cliente (Fase 2)
    cliente = forms.ModelChoiceField(
        label="Cliente",
        queryset=None,  # Se inicializará en __init__
        required=False,
        empty_label="Sin cliente (opcional)",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'cliente_select'
        }),
        help_text="Asocia esta optimización a un cliente"
    )
    
    # Campo para asociar proyecto (Fase 3)
    proyecto = forms.ModelChoiceField(
        label="Proyecto",
        queryset=None,  # Se inicializará en __init__
        required=False,
        empty_label="Sin proyecto (opcional)",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'proyecto_select'
        }),
        help_text="Asocia esta optimización a un proyecto"
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        
        # Verificar si hay datos POST antes de llamar a super()
        # En Django, cuando se pasa TableroForm(request.POST), args[0] contiene los datos
        # Cuando se pasa TableroForm(user=request.user), args está vacío
        has_post_data = len(args) > 0 and args[0] is not None
        
        # Extraer initial si existe (para respetar valores pasados desde la vista)
        initial_from_kwargs = kwargs.pop('initial', None)
        
        # CORREGIDO: Guardar el valor inicial por defecto del margen de corte antes de llamar a super()
        # para poder comparar después si se estableció explícitamente
        margen_corte_default = 3.0  # Valor por defecto del campo
        
        super().__init__(*args, **kwargs)
        
        # Actualizar queryset de materiales PRIMERO para incluir los del usuario y predefinidos
        # Esto es necesario antes de aplicar valores iniciales
        # CORREGIDO: Definir materiales siempre para que esté disponible en todo el método
        if user:
            materiales = Material.objects.filter(
                models.Q(usuario=user) | models.Q(es_predefinido=True)
            ).order_by('-es_predefinido', 'nombre')
            self.fields['material'].queryset = materiales
        else:
            materiales = Material.objects.filter(es_predefinido=True)
            self.fields['material'].queryset = materiales
        
        # CORREGIDO: Rastrear qué campos se establecieron explícitamente desde initial_from_kwargs
        # También guardar los valores iniciales por defecto para comparar después
        valores_iniciales_por_defecto = {
            'margen_corte': self.fields['margen_corte'].initial,
            'permitir_rotacion': self.fields['permitir_rotacion'].initial,
        }
        campos_establecidos_explicitamente = set()
        
        # Si se pasó initial desde la vista, aplicarlo después de establecer el queryset
        if initial_from_kwargs:
            for field_name, value in initial_from_kwargs.items():
                if field_name in self.fields:
                    campos_establecidos_explicitamente.add(field_name)
                    # Convertir material a objeto si es necesario
                    if field_name == 'material' and value is not None:
                        try:
                            # Si value es un objeto Material, verificar que esté en el queryset
                            if isinstance(value, Material):
                                if value in materiales:
                                    self.fields[field_name].initial = value
                            # Si value es un ID (int o str), buscar el material
                            elif isinstance(value, (int, str)):
                                material_obj = Material.objects.get(pk=value)
                                if material_obj in materiales:
                                    self.fields[field_name].initial = material_obj
                        except (Material.DoesNotExist, ValueError, AttributeError):
                            # Si no se encuentra, no establecer initial
                            pass
                    else:
                        # Para campos numéricos, asegurar que el valor sea del tipo correcto
                        if field_name in ['margen_corte', 'precio_tablero', 'mano_obra']:
                            if value is not None:
                                # CORREGIDO: Asegurar conversión correcta a float
                                try:
                                    valor_float = float(value)
                                    # Para margen_corte, si es un entero, guardarlo como entero para evitar decimales
                                    if field_name == 'margen_corte' and valor_float == int(valor_float):
                                        self.fields[field_name].initial = int(valor_float)
                                    else:
                                        self.fields[field_name].initial = valor_float
                                except (ValueError, TypeError):
                                    # Si no se puede convertir, mantener el valor por defecto
                                    pass
                            else:
                                # Si no hay valor, mantener el valor por defecto del campo
                                pass
                        elif field_name == 'permitir_rotacion':
                            if value is not None:
                                self.fields[field_name].initial = bool(value)
                        else:
                            self.fields[field_name].initial = value
            
            # Actualizar queryset de clientes
            if user:
                self.fields['cliente'].queryset = Cliente.objects.filter(usuario=user).order_by('nombre')
            else:
                self.fields['cliente'].queryset = Cliente.objects.none()
            
            # Actualizar queryset de proyectos
            if user:
                self.fields['proyecto'].queryset = Proyecto.objects.filter(usuario=user).order_by('-fecha_creacion')
            else:
                self.fields['proyecto'].queryset = Proyecto.objects.none()
        else:
            # Si no hay initial_from_kwargs, aún necesitamos establecer los querysets si hay user
            if user:
                self.fields['cliente'].queryset = Cliente.objects.filter(usuario=user).order_by('nombre')
                self.fields['proyecto'].queryset = Proyecto.objects.filter(usuario=user).order_by('-fecha_creacion')
            else:
                self.fields['cliente'].queryset = Cliente.objects.none()
                self.fields['proyecto'].queryset = Proyecto.objects.none()
        
        # Aplicar valores predeterminados del perfil del usuario (solo si no hay datos POST)
        # CORREGIDO: Solo aplicar predeterminados si el campo NO fue establecido explícitamente desde initial_from_kwargs
        if user and not has_post_data:
            try:
                perfil = user.perfil
                perfil.refresh_from_db()  # Asegurar que tenemos los valores más recientes
                
                # Unidad de medida predeterminada (solo si no se pasó en initial)
                if perfil.unidad_medida_predeterminada and 'unidad_medida' not in campos_establecidos_explicitamente:
                    # Normalizar unidad para compatibilidad
                    unidad = perfil.unidad_medida_predeterminada
                    if unidad == 'pulgadas':
                        unidad = 'in'
                    # Ahora el formulario soporta todas las unidades (cm, m, mm, in, ft)
                    # Verificar que la unidad esté en las opciones del formulario
                    if unidad in [choice[0] for choice in self.fields['unidad_medida'].choices]:
                        self.fields['unidad_medida'].initial = unidad
                    else:
                        # Si por alguna razón no está, usar cm como fallback
                        self.fields['unidad_medida'].initial = 'cm'
                
                # Margen de corte predeterminado (convertir de cm a mm)
                # CORREGIDO: Siempre aplicar el valor del perfil si no fue establecido explícitamente
                # La vista ya pasa el valor en initial_data, pero si por alguna razón no se pasó,
                # aplicar el valor del perfil directamente
                if perfil.margen_corte_predeterminado is not None:
                    # Solo aplicar si NO fue establecido explícitamente desde initial_from_kwargs
                    # Si la vista lo pasó, ya está establecido y no necesitamos hacer nada más
                    if 'margen_corte' not in campos_establecidos_explicitamente:
                        margen_mm = float(perfil.margen_corte_predeterminado) * 10  # cm a mm
                        margen_mm_redondeado = round(margen_mm, 1)
                        # Si es un entero, guardar como entero para evitar decimales innecesarios
                        if margen_mm_redondeado == int(margen_mm_redondeado):
                            self.fields['margen_corte'].initial = int(margen_mm_redondeado)
                        else:
                            self.fields['margen_corte'].initial = margen_mm_redondeado
                
                # Rotación automática predeterminada
                if perfil.rotacion_automatica_predeterminada is not None and 'permitir_rotacion' not in campos_establecidos_explicitamente:
                    self.fields['permitir_rotacion'].initial = perfil.rotacion_automatica_predeterminada
                    
            except AttributeError:
                # Si el usuario no tiene perfil, usar valores por defecto
                pass
        elif not user:
            # Si no hay usuario, solo materiales predefinidos
            self.fields['cliente'].queryset = Cliente.objects.none()
            self.fields['proyecto'].queryset = Proyecto.objects.none()
    
    def clean(self):
        from .utils import convertir_a_cm
        
        cleaned_data = super().clean()
        ancho = cleaned_data.get('ancho')
        alto = cleaned_data.get('alto')
        unidad = cleaned_data.get('unidad_medida', 'cm')
        
        # Validar que ambos campos estén presentes
        if not ancho:
            raise forms.ValidationError("El ancho del tablero es requerido.")
        if not alto:
            raise forms.ValidationError("El alto del tablero es requerido.")
        
        # Convertir a cm para validar rangos (mínimo 50cm, máximo 300cm)
        ancho_cm = convertir_a_cm(ancho, unidad)
        alto_cm = convertir_a_cm(alto, unidad)
        
        # Validar rangos en cm (equivalente a 10-300 cm) - Reducido el mínimo para permitir tableros más pequeños
        if ancho_cm < 10 or ancho_cm > 300:
            raise forms.ValidationError(f"El ancho debe estar entre {self._get_min_unidad(unidad)} y {self._get_max_unidad(unidad)} {unidad}.")
        if alto_cm < 10 or alto_cm > 300:
            raise forms.ValidationError(f"El alto debe estar entre {self._get_min_unidad(unidad)} y {self._get_max_unidad(unidad)} {unidad}.")
        
        # Validar margen de corte (siempre en mm, máximo 10 mm)
        margen = cleaned_data.get('margen_corte')
        if margen is not None:
            if margen < 0:
                raise forms.ValidationError("El margen de corte no puede ser negativo.")
            if margen > 10:  # Máximo 10 mm
                raise forms.ValidationError("El margen de corte no puede ser mayor a 10 mm.")
        
        return cleaned_data
    
    def _get_min_unidad(self, unidad):
        """Retorna el valor mínimo en la unidad especificada (equivalente a 10cm)"""
        from .utils import convertir_desde_cm
        return round(convertir_desde_cm(10, unidad), 2)
    
    def _get_max_unidad(self, unidad):
        """Retorna el valor máximo en la unidad especificada (equivalente a 300cm)"""
        from .utils import convertir_desde_cm
        return round(convertir_desde_cm(300, unidad), 2)

class PiezaForm(forms.Form):
    nombre = forms.CharField(
        label="Nombre de la pieza",
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Puerta, Cajón, Estante'
        }),
        help_text="Opcional: identifica esta pieza"
    )
    ancho = forms.FloatField(
        label="Ancho (cm)",
        min_value=0.1,
        max_value=300,
        required=False,  # Hacerlo opcional
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ancho',
            'step': '0.01'
        })
    )
    alto = forms.FloatField(
        label="Alto (cm)",
        min_value=0.1,
        max_value=300,
        required=False,  # Hacerlo opcional
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Alto',
            'step': '0.01'
        })
    )
    cantidad = forms.IntegerField(
        label="Cantidad",
        min_value=1,
        max_value=100,
        initial=1,
        required=False,  # Hacerlo opcional
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '1'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        ancho = cleaned_data.get('ancho')
        alto = cleaned_data.get('alto')
        cantidad = cleaned_data.get('cantidad')
        nombre = cleaned_data.get('nombre', '').strip()
        
        # Si TODOS los campos están vacíos, el formulario es válido (formulario vacío)
        todos_vacios = not ancho and not alto and not cantidad and not nombre
        
        if todos_vacios:
            # Formulario completamente vacío - es válido, se ignorará
            return cleaned_data
        
        # Si alguno está lleno, ancho y alto son requeridos
        if not ancho:
            raise forms.ValidationError("El ancho es requerido si ingresas una pieza.")
        if not alto:
            raise forms.ValidationError("El alto es requerido si ingresas una pieza.")
        if not cantidad:
            cleaned_data['cantidad'] = 1  # Valor por defecto
        
        if ancho and alto:
            if ancho <= 0 or alto <= 0:
                raise forms.ValidationError("Las dimensiones deben ser positivas.")
        
        return cleaned_data


class MaterialForm(forms.ModelForm):
    """Formulario para crear y editar materiales"""
    
    class Meta:
        from .models import Material
        model = Material
        fields = ['nombre', 'ancho', 'alto', 'unidad_medida', 'precio', 'descripcion']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: MDF 18mm, Contrachapado'
            }),
            'ancho': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.1'
            }),
            'alto': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.1'
            }),
            'unidad_medida': forms.Select(attrs={
                'class': 'form-select'
            }),
            'precio': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Opcional'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción opcional del material'
            }),
        }
        labels = {
            'nombre': 'Nombre del Material',
            'ancho': 'Ancho',
            'alto': 'Alto',
            'unidad_medida': 'Unidad de Medida',
            'precio': 'Precio por Tablero',
            'descripcion': 'Descripción',
        }
        help_texts = {
            'precio': 'Precio en pesos chilenos (opcional)',
        }
    
    def clean(self):
        cleaned_data = super().clean()
        ancho = cleaned_data.get('ancho')
        alto = cleaned_data.get('alto')
        
        if ancho and ancho <= 0:
            raise forms.ValidationError({'ancho': 'El ancho debe ser mayor a 0.'})
        
        if alto and alto <= 0:
            raise forms.ValidationError({'alto': 'El alto debe ser mayor a 0.'})
        
        return cleaned_data


class ClienteForm(forms.ModelForm):
    """Formulario para crear y editar clientes"""
    
    class Meta:
        model = Cliente
        fields = ['nombre', 'rut', 'email', 'telefono', 'direccion', 'notas']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Juan Pérez, Empresa XYZ S.A.'
            }),
            'rut': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 12.345.678-9'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'cliente@ejemplo.com'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: +56 9 1234 5678'
            }),
            'direccion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Dirección completa'
            }),
            'notas': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Notas adicionales sobre el cliente'
            }),
        }
        labels = {
            'nombre': 'Nombre o Razón Social',
            'rut': 'RUT / Identificación',
            'email': 'Correo Electrónico',
            'telefono': 'Teléfono',
            'direccion': 'Dirección',
            'notas': 'Notas',
        }
    
    def clean_rut(self):
        rut = self.cleaned_data.get('rut', '').strip()
        # Validación básica de RUT chileno (opcional, puede estar vacío)
        if rut:
            # Remover puntos y guiones para validar
            rut_limpio = rut.replace('.', '').replace('-', '')
            if not rut_limpio[:-1].isdigit() or (rut_limpio[-1] not in '0123456789Kk'):
                raise forms.ValidationError('Formato de RUT inválido. Use formato: 12.345.678-9')
        return rut


class PresupuestoForm(forms.ModelForm):
    """Formulario para crear y editar presupuestos con múltiples optimizaciones"""
    
    # Campo opcional para escribir el nombre del cliente directamente
    nombre_cliente_nuevo = forms.CharField(
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'O escribe el nombre del cliente aquí'
        }),
        label='Nombre del Cliente (Alternativa)',
        help_text='Si escribes un nombre aquí, se creará o buscará el cliente automáticamente. Deja vacío si seleccionaste un cliente arriba.'
    )
    
    class Meta:
        model = Presupuesto
        fields = ['cliente', 'optimizaciones', 'precio_tablero', 'mano_obra', 'fecha_validez', 'notas', 'estado', 'proyecto']
        widgets = {
            'cliente': forms.Select(attrs={
                'class': 'form-select'
            }),
            'optimizaciones': forms.CheckboxSelectMultiple(attrs={
                'class': 'form-check-input'
            }),
            'precio_tablero': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'mano_obra': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'fecha_validez': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'format': '%Y-%m-%d'
            }),
            'notas': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Notas adicionales para el cliente'
            }),
            'estado': forms.Select(attrs={
                'class': 'form-select'
            }),
            'proyecto': forms.Select(attrs={
                'class': 'form-select'
            }),
        }
        labels = {
            'cliente': 'Cliente',
            'optimizaciones': 'Optimizaciones',
            'precio_tablero': 'Precio por Tablero',
            'mano_obra': 'Mano de Obra',
            'fecha_validez': 'Válido Hasta',
            'notas': 'Notas',
            'estado': 'Estado',
            'proyecto': 'Proyecto (Opcional)',
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        instance = kwargs.get('instance', None)
        super().__init__(*args, **kwargs)
        
        # Hacer el campo cliente opcional
        self.fields['cliente'].required = False
        
        if user:
            # Filtrar clientes del usuario
            self.fields['cliente'].queryset = Cliente.objects.filter(usuario=user).order_by('nombre')
            # Filtrar optimizaciones del usuario
            from .models import Optimizacion
            if instance:
                # Si es edición, mostrar optimizaciones que ya están en este presupuesto o que no tienen presupuesto
                optimizaciones_queryset = Optimizacion.objects.filter(
                    usuario=user
                ).filter(
                    Q(presupuestos__isnull=True) | Q(presupuestos=instance)
                ).distinct().order_by('-fecha')
                # Pre-seleccionar las optimizaciones que ya están en el presupuesto
                self.fields['optimizaciones'].initial = list(instance.optimizaciones.values_list('pk', flat=True))
            else:
                # Si es creación, mostrar todas las optimizaciones del usuario
                optimizaciones_queryset = Optimizacion.objects.filter(usuario=user).order_by('-fecha')
            self.fields['optimizaciones'].queryset = optimizaciones_queryset
            # Filtrar proyectos del usuario
            self.fields['proyecto'].queryset = Proyecto.objects.filter(usuario=user).order_by('-fecha_creacion')
        
        # Si es edición, asegurar que la fecha_validez se muestre correctamente
        if instance and instance.fecha_validez:
            # Convertir la fecha a formato ISO (YYYY-MM-DD) para el campo type='date'
            self.fields['fecha_validez'].initial = instance.fecha_validez.strftime('%Y-%m-%d')
        
        # Si es edición y hay cliente, prellenar el nombre
        if instance and instance.cliente:
            self.fields['nombre_cliente_nuevo'].initial = instance.cliente.nombre


class ProyectoForm(forms.ModelForm):
    """Formulario para crear y editar proyectos"""
    
    # Campo personalizado para seleccionar múltiples optimizaciones
    optimizaciones = forms.ModelMultipleChoiceField(
        queryset=Optimizacion.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        label='Optimizaciones (Opcional)',
        help_text='Selecciona las optimizaciones que deseas asociar a este proyecto.'
    )
    
    class Meta:
        model = Proyecto
        fields = ['nombre', 'descripcion', 'cliente', 'fecha_inicio', 'fecha_fin', 'estado']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Cocina Integral, Mueble de Sala'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Descripción del proyecto'
            }),
            'cliente': forms.Select(attrs={
                'class': 'form-select'
            }),
            'fecha_inicio': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'format': '%Y-%m-%d'
            }),
            'fecha_fin': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'format': '%Y-%m-%d'
            }),
            'estado': forms.Select(attrs={
                'class': 'form-select'
            }),
        }
        labels = {
            'nombre': 'Nombre del Proyecto',
            'descripcion': 'Descripción',
            'cliente': 'Cliente',
            'fecha_inicio': 'Fecha de Inicio',
            'fecha_fin': 'Fecha de Finalización',
            'estado': 'Estado',
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        instance = kwargs.get('instance', None)
        super().__init__(*args, **kwargs)
        
        if user:
            # Filtrar clientes del usuario
            self.fields['cliente'].queryset = Cliente.objects.filter(usuario=user).order_by('nombre')
            
            # Filtrar optimizaciones del usuario que no estén ya en otro proyecto (o que estén en este proyecto si es edición)
            if instance:
                # Si es edición, mostrar optimizaciones que ya están en este proyecto o que no tienen proyecto
                optimizaciones_queryset = Optimizacion.objects.filter(
                    usuario=user
                ).filter(
                    Q(proyecto__isnull=True) | Q(proyecto=instance)
                ).order_by('-fecha')
                # Pre-seleccionar las optimizaciones que ya están en el proyecto
                self.fields['optimizaciones'].initial = list(instance.optimizacion_set.values_list('pk', flat=True))
            else:
                # Si es creación, mostrar solo optimizaciones sin proyecto
                optimizaciones_queryset = Optimizacion.objects.filter(
                    usuario=user,
                    proyecto__isnull=True
                ).order_by('-fecha')
            
            self.fields['optimizaciones'].queryset = optimizaciones_queryset
        
        # Si es edición, asegurar que las fechas se muestren correctamente
        if instance:
            if instance.fecha_inicio:
                self.fields['fecha_inicio'].initial = instance.fecha_inicio.strftime('%Y-%m-%d')
            if instance.fecha_fin:
                self.fields['fecha_fin'].initial = instance.fecha_fin.strftime('%Y-%m-%d')


class PlantillaForm(forms.ModelForm):
    """Formulario para crear y editar plantillas"""
    
    class Meta:
        model = Plantilla
        fields = ['nombre', 'descripcion', 'categoria', 'ancho_tablero', 'alto_tablero', 'unidad_medida', 'piezas', 'permitir_rotacion', 'margen_corte']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Cocina Estándar, Mueble de TV'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción de la plantilla'
            }),
            'categoria': forms.Select(attrs={
                'class': 'form-select'
            }),
            'ancho_tablero': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.1'
            }),
            'alto_tablero': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.1'
            }),
            'unidad_medida': forms.Select(attrs={
                'class': 'form-select'
            }),
            'piezas': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 8,
                'placeholder': 'Formato: nombre,ancho,alto,cantidad (una por línea)\n\nEjemplos:\nPuerta,80,200,2\nCajón,40,50,4\nFondo,85,198,1\nTravesaño,70,2,4\n\nCada línea debe tener EXACTAMENTE 4 valores separados por comas.'
            }),
            'permitir_rotacion': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'margen_corte': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': '0',
                'max': '10'
            }),
        }
        labels = {
            'nombre': 'Nombre de la Plantilla',
            'descripcion': 'Descripción',
            'categoria': 'Categoría',
            'ancho_tablero': 'Ancho del Tablero (cm)',
            'alto_tablero': 'Alto del Tablero (cm)',
            'unidad_medida': 'Unidad de Medida',
            'piezas': 'Piezas (formato: nombre,ancho,alto,cantidad)',
            'permitir_rotacion': 'Permitir Rotación',
            'margen_corte': 'Margen de Corte (mm)',
        }
    
    def clean_piezas(self):
        piezas = self.cleaned_data.get('piezas', '').strip()
        if not piezas:
            raise forms.ValidationError("Debes ingresar al menos una pieza.")
        
        # Validar formato
        lineas_validas = 0
        for linea in piezas.splitlines():
            if linea.strip():
                partes = linea.split(',')
                if len(partes) != 4:
                    raise forms.ValidationError(
                        f"❌ Línea inválida: '{linea}'\n\n"
                        f"Esperado: nombre,ancho,alto,cantidad\n\n"
                        f"Ejemplo correcto:\n"
                        f"Puerta,80,200,2"
                    )
                try:
                    ancho = float(partes[1].strip())
                    alto = float(partes[2].strip())
                    cantidad = int(partes[3].strip())
                    
                    if ancho <= 0 or alto <= 0 or cantidad <= 0:
                        raise forms.ValidationError(
                            f"❌ Valores en línea '{linea}' no pueden ser negativos o cero.\n"
                            f"Ancho: {ancho}, Alto: {alto}, Cantidad: {cantidad}"
                        )
                except ValueError as e:
                    raise forms.ValidationError(
                        f"❌ Valores numéricos inválidos en línea: '{linea}'\n\n"
                        f"Asegúrate de que:\n"
                        f"- Nombre: texto (puede incluir espacios)\n"
                        f"- Ancho: número\n"
                        f"- Alto: número\n"
                        f"- Cantidad: número entero"
                    )
                lineas_validas += 1
        
        if lineas_validas == 0:
            raise forms.ValidationError("Debes ingresar al menos una pieza válida.")
        
        return piezas
    
    def clean_margen_corte(self):
        margen = self.cleaned_data.get('margen_corte')
        if margen is not None:
            # Convertir de mm a cm para almacenar
            return margen / 10.0
        return 0.3  # Valor por defecto
