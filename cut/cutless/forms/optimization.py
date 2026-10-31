from django import forms
from django.db.models import Q

from ..models import Material, Cliente, Proyecto

class NombreOptimizacionForm(forms.Form):
    nombre_optimizacion = forms.CharField(label='Nombre del trabajo (opcional)',
        max_length=100, required=False,
        widget=forms.TextInput(attrs={'class':'form-control', 'id':'nombre_optimizacion',
            'placeholder':'Ej.: Mueble de cocina', 'aria-describedby':'nombre_optimizacion_ayuda'}))

    def clean_nombre_optimizacion(self):
        return ' '.join(self.cleaned_data.get('nombre_optimizacion', '').split())


class MedidasClarasMixin:
    minimo_cm = 10
    maximo_cm = 300
    objeto_medida = 'tablero'

    def configurar_medidas(self, unidad=None):
        self.unidad_medidas = unidad or (self.data.get('unidad_medida') if self.is_bound else self['unidad_medida'].value()) or 'cm'
        if self.unidad_medidas not in ('cm', 'm', 'mm', 'in', 'ft'):
            self.unidad_medidas = 'cm'
        for nombre in ('ancho', 'alto'):
            field = self.fields[nombre]
            field.error_messages['invalid'] = f'Escribe un número válido para el {nombre} del {self.objeto_medida}, en {self.unidad_medidas}.'
            field.widget.attrs['aria-describedby'] = f'{self.add_prefix(nombre)}_rango'
            field.help_text = self.ayuda_medidas()
            field.label = f'{nombre.capitalize()} del {self.objeto_medida} ({self.unidad_medidas})'

    def ayuda_medidas(self):
        from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR
        factor = Decimal({'cm': '1', 'm': '100', 'mm': '0.1', 'in': '2.54', 'ft': '30.48'}[self.unidad_medidas])
        def limite(valor, redondeo):
            numero = (Decimal(str(valor)) / factor).quantize(Decimal('0.000001'), rounding=redondeo)
            return format(numero.normalize(), 'f').replace('.', ',')
        minimo = limite(self.minimo_cm, ROUND_CEILING)
        maximo = limite(self.maximo_cm, ROUND_FLOOR)
        return f'Rango permitido: de {minimo} a {maximo} {self.unidad_medidas} por lado.'

    def validar_medidas(self, cleaned_data, obligatorias=True):
        from ..units import convertir_a_cm
        for nombre in ('ancho', 'alto'):
            if nombre in self.errors:
                continue
            valor = cleaned_data.get(nombre)
            if valor is None:
                if obligatorias:
                    self.add_error(nombre, f'Escribe el {nombre} del {self.objeto_medida} en {self.unidad_medidas}.')
                continue
            cm = convertir_a_cm(valor, self.unidad_medidas)
            if cm < self.minimo_cm - 1e-9 or cm > self.maximo_cm + 1e-9:
                ingresado = format(valor, '.12g').replace('.', ',')
                motivo = 'demasiado alto' if cm > self.maximo_cm else 'demasiado bajo'
                self.add_error(nombre, f'El {nombre} del {self.objeto_medida} es {motivo}: ingresaste {ingresado} {self.unidad_medidas}. {self.ayuda_medidas()} Revisa el valor o la unidad seleccionada.')
        return cleaned_data


class TableroForm(MedidasClarasMixin, NombreOptimizacionForm):
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
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 122',
            'id': 'ancho_tablero',
            'step': 'any'
        }),
        help_text="Ingresa el ancho del tablero"
    )
    
    alto = forms.FloatField(
        label="Alto del tablero",
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 244',
            'id': 'alto_tablero',
            'step': 'any'
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
        error_messages={
            'min_value': 'El ancho de sierra no puede ser negativo. Rango permitido: de 0 a 10 mm; 0 significa sin separación.',
            'max_value': 'El ancho de sierra supera el máximo permitido de 10 mm. Revisa el valor; este campo siempre se expresa en mm.',
            'invalid': 'Escribe un número válido para el ancho de sierra, en mm.',
        },
        initial=3,  # 3 mm es un valor típico
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '3',
            'step': '0.1',
            'id': 'margen_corte',
            'aria-describedby': 'margen_corte_rango',
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
                Q(usuario=user) | Q(es_predefinido=True)
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
    
        self.configurar_medidas()

    def clean(self):
        return self.validar_medidas(super().clean())

class PiezaForm(MedidasClarasMixin, forms.Form):
    minimo_cm = 0.1
    objeto_medida = 'pieza'

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
        required=False,  # Hacerlo opcional
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ancho',
            'step': 'any'
        })
    )
    alto = forms.FloatField(
        label="Alto (cm)",
        required=False,  # Hacerlo opcional
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Alto',
            'step': 'any'
        })
    )
    cantidad = forms.IntegerField(
        label="Cantidad",
        min_value=1,
        max_value=100,
        error_messages={
            'min_value': 'La cantidad debe ser de al menos 1 pieza por tipo.',
            'max_value': 'La cantidad máxima es de 100 piezas iguales por tipo. Reduce la cantidad antes de generar el plan.',
            'invalid': 'Escribe una cantidad entera de 1 a 100 piezas por tipo.',
        },
        initial=1,
        required=False,  # Hacerlo opcional
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '1'
        })
    )

    def __init__(self, *args, **kwargs):
        unidad = kwargs.pop('unidad_medida', None)
        super().__init__(*args, **kwargs)
        self.configurar_medidas(unidad or (self.data.get('unidad_medida') if self.is_bound else 'cm') or 'cm')
        self.fields['cantidad'].widget.attrs['aria-describedby'] = f'{self.add_prefix("cantidad")}_rango'

    def clean(self):
        cleaned_data = super().clean()
        activa = any(self.data.get(self.add_prefix(nombre)) not in (None, '')
                     for nombre in ('nombre', 'ancho', 'alto', 'cantidad')) if self.is_bound else bool(cleaned_data)
        if activa:
            self.validar_medidas(cleaned_data)
            if cleaned_data.get('cantidad') is None and 'cantidad' not in self.errors:
                cleaned_data['cantidad'] = 1
        return cleaned_data
