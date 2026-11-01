from django import forms

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
        self.fields['fecha_validez'].widget.format = '%Y-%m-%d'
        
        for campo in ('cliente', 'optimizaciones', 'proyecto'):
            self.fields[campo].queryset = self.fields[campo].queryset.none()
        if user:
            # Filtrar clientes del usuario
            self.fields['cliente'].queryset = Cliente.objects.filter(usuario=user).order_by('nombre')
            # Filtrar optimizaciones del usuario
            if instance:
                # Una optimización puede cotizarse en varios presupuestos, igual que al crear.
                optimizaciones_queryset = Optimizacion.objects.filter(usuario=user).order_by('-fecha')
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
        
        # No duplicar el cliente seleccionado en la alternativa de creación.
        self.fields['nombre_cliente_nuevo'].initial = ''

    def clean(self):
        from decimal import Decimal
        datos = super().clean()
        if datos.get('cliente') and datos.get('nombre_cliente_nuevo'):
            self.add_error('nombre_cliente_nuevo', 'Selecciona un cliente o escribe uno nuevo, no ambos.')
        for campo in ('precio_tablero', 'mano_obra'):
            if datos.get(campo) is not None and datos[campo] < 0:
                self.add_error(campo, 'El importe no puede ser negativo.')
        precio, mano = datos.get('precio_tablero'), datos.get('mano_obra')
        seleccion = datos.get('optimizaciones')
        if precio is not None and mano is not None and seleccion is not None:
            total = precio * sum(opt.num_tableros for opt in seleccion) + mano
            if total > Decimal('99999999.99'):
                self.add_error('precio_tablero', 'El total supera el máximo admitido: $99.999.999,99.')
        return datos
