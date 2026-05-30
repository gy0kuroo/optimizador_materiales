from django import forms

from ..models import Cliente

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
