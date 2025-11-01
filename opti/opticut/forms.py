from django import forms

class TableroForm(forms.Form):
    ancho = forms.IntegerField(
        label="Ancho del tablero (cm)",
        min_value=50,
        max_value=300,
        initial=244,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 244'
        }),
        help_text="Valor entre 50 y 300 cm"
    )
    alto = forms.IntegerField(
        label="Alto del tablero (cm)",
        min_value=50,
        max_value=300,
        initial=122,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 122'
        }),
        help_text="Valor entre 50 y 300 cm"
    )

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
    ancho = forms.IntegerField(
        label="Ancho (cm)",
        min_value=1,
        max_value=300,
        required=False,  # Hacerlo opcional
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ancho'
        })
    )
    alto = forms.IntegerField(
        label="Alto (cm)",
        min_value=1,
        max_value=300,
        required=False,  # Hacerlo opcional
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Alto'
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