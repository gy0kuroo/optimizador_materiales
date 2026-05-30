from django import forms

from ..models import Material

class MaterialForm(forms.ModelForm):
    """Formulario para crear y editar materiales"""
    
    class Meta:
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
