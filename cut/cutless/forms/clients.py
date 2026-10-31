import re

from django import forms

from ..models import Cliente

class ClienteForm(forms.ModelForm):
    """Formulario para crear y editar clientes"""
    
    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_nombre(self):
        nombre = self.cleaned_data['nombre']
        if self.user and Cliente.objects.filter(usuario=self.user, nombre=nombre).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Ya tienes un cliente con este nombre.')
        return nombre

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
                'placeholder': 'Ej.: 12345678-9'
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
            'rut': 'RUT',
            'email': 'Correo Electrónico',
            'telefono': 'Teléfono',
            'direccion': 'Dirección',
            'notas': 'Notas',
        }
    
    def clean_rut(self):
        rut = self.cleaned_data.get('rut', '').strip().upper()
        if not rut:
            return ''
        # Aceptar escritura anterior con puntos; guardar siempre un formato único.
        compacto = rut.replace('.', '')
        coincidencia = re.fullmatch(r'([0-9]{1,8})-?([0-9K])', compacto)
        if not coincidencia:
            raise forms.ValidationError('Escribe el RUT sin puntos y con guion antes del dígito verificador. Ejemplo: 12345678-9.')
        return f'{coincidencia[1]}-{coincidencia[2]}'
