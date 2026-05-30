from django import forms
from django.db.models import Q

from ..models import Presupuesto, Optimizacion, Cliente, Proyecto

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
