import math

from django import forms

from ..models import Material
from ..units import convertir_a_cm, convertir_desde_cm

class MaterialForm(forms.ModelForm):
    """Formulario para crear y editar materiales"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            unidad = self.instance.unidad_medida or 'cm'
            self.initial['ancho'] = convertir_desde_cm(self.instance.ancho, unidad)
            self.initial['alto'] = convertir_desde_cm(self.instance.alto, unidad)

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
        datos = super().clean()
        unidad = datos.get('unidad_medida')
        for campo in ('ancho', 'alto'):
            valor = datos.get(campo)
            if valor is not None:
                if not math.isfinite(valor) or valor <= 0:
                    self.add_error(campo, 'La medida debe ser un número mayor que cero.')
                elif unidad:
                    datos[campo] = convertir_a_cm(valor, unidad)
        precio = datos.get('precio')
        if precio is not None and precio < 0:
            self.add_error('precio', 'El precio no puede ser negativo.')
        return datos
