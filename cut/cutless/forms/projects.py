from django import forms

from ..models import Proyecto, Cliente, Optimizacion

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
