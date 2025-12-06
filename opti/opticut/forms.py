from django import forms

class TableroForm(forms.Form):
    UNIDADES_CHOICES = [
        ('cm', 'Centímetros (cm)'),
        ('m', 'Metros (m)'),
        ('in', 'Pulgadas (in)'),
        ('ft', 'Pies (ft)'),
    ]
    
    unidad_medida = forms.ChoiceField(
        label="Unidad de medida",
        choices=UNIDADES_CHOICES,
        initial='cm',
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
        
        # Validar rangos en cm (equivalente a 50-300 cm)
        if ancho_cm < 50 or ancho_cm > 300:
            raise forms.ValidationError(f"El ancho debe estar entre {self._get_min_unidad(unidad)} y {self._get_max_unidad(unidad)} {unidad}.")
        if alto_cm < 50 or alto_cm > 300:
            raise forms.ValidationError(f"El alto debe estar entre {self._get_min_unidad(unidad)} y {self._get_max_unidad(unidad)} {unidad}.")
        
        return cleaned_data
    
    def _get_min_unidad(self, unidad):
        """Retorna el valor mínimo en la unidad especificada (equivalente a 50cm)"""
        from .utils import convertir_desde_cm
        return round(convertir_desde_cm(50, unidad), 2)
    
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
        
        # Si alguno está lleno, todos deben estar llenos
        tiene_datos = any([ancho, alto, cantidad])
        
        if tiene_datos:
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