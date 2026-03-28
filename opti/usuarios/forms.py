from django import forms
from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from decimal import Decimal
from .models import PerfilUsuario

class RegistroForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class UsuarioEdicionForm(forms.ModelForm):
    password1 = forms.CharField(
        label='Nueva contraseña',
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text='Solo si deseas cambiar la contraseña'
    )
    password2 = forms.CharField(
        label='Confirmar contraseña',
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )

    class Meta:
        model = User
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password1')
        p2 = cleaned_data.get('password2')

        if p1 or p2:
            if p1 != p2:
                raise forms.ValidationError('Las contraseñas no coinciden')
            if len(p1) < 8:
                raise forms.ValidationError('La contraseña debe tener al menos 8 caracteres')

        return cleaned_data


class PermisosUsuarioForm(forms.ModelForm):
    """Formulario para editar permisos y funcionalidades del usuario"""
    
    class Meta:
        model = PerfilUsuario
        fields = [
            'puede_crear_plantillas',
            'puede_comparar_optimizaciones',
            'puede_crear_clientes',
            'puede_crear_proyectos',
            'puede_crear_presupuestos',
            'puede_crear_materiales',
            'puede_ver_estadisticas',
            'puede_ver_historial_costos',
        ]
        widgets = {
            'puede_crear_plantillas': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'puede_comparar_optimizaciones': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'puede_crear_clientes': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'puede_crear_proyectos': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'puede_crear_presupuestos': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'puede_crear_materiales': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'puede_ver_estadisticas': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'puede_ver_historial_costos': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'puede_crear_plantillas': 'Crear/Editar Plantillas',
            'puede_comparar_optimizaciones': 'Comparar Optimizaciones',
            'puede_crear_clientes': 'Crear/Editar Clientes',
            'puede_crear_proyectos': 'Crear/Editar Proyectos',
            'puede_crear_presupuestos': 'Crear/Editar Presupuestos',
            'puede_crear_materiales': 'Crear/Editar Materiales',
            'puede_ver_estadisticas': 'Ver Estadísticas',
            'puede_ver_historial_costos': 'Ver Historial de Costos',
        }


class PerfilForm(forms.ModelForm):
    """Formulario para editar información del perfil"""
    username = forms.CharField(
        label="Nombre de usuario",
        max_length=150,
        required=True,
        help_text="Requerido. 150 caracteres o menos. Únicamente letras, dígitos y @/./+/-/_",
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        error_messages={
            'required': 'El nombre de usuario es obligatorio.',
            'max_length': 'El nombre de usuario no puede tener más de 150 caracteres.'
        }
    )
    email = forms.EmailField(
        label="Correo electrónico",
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
        error_messages={
            'required': 'El correo electrónico es obligatorio.',
            'invalid': 'Por favor ingresa un correo electrónico válido.'
        }
    )
    timeout_sesion = forms.IntegerField(
        label="Timeout de sesión (minutos)",
        required=False,
        min_value=0,
        max_value=480,  # Máximo 8 horas
        help_text="Tiempo de inactividad antes de cerrar sesión automáticamente. 0 para desactivar. Déjalo vacío para usar 30 minutos por defecto.",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '480', 'step': '5'}),
        error_messages={
            'min_value': 'El tiempo mínimo es 0 minutos.',
            'max_value': 'El tiempo máximo es 480 minutos (8 horas).',
            'invalid': 'Por favor ingresa un número válido.'
        }
    )
    tema_preferido = forms.ChoiceField(
        label="Tema preferido",
        choices=[('light', 'Claro'), ('dark', 'Oscuro'), ('auto', 'Automático')],
        required=True,
        widget=forms.Select(attrs={'class': 'form-control', 'data-pref-key': 'tema_preferido'}),
        error_messages={
            'required': 'Selecciona un tema preferido.'
        }
    )

    tamanio_fuente = forms.ChoiceField(
        label="Tamaño de letra",
        choices=[
            ('small', 'Pequeño'),
            ('normal', 'Normal'),
            ('large', 'Grande'),
            ('xlarge', 'Extra grande')
        ],
        required=True,
        widget=forms.Select(attrs={'class': 'form-control', 'data-pref-key': 'tamanio_fuente'}),
        help_text="Aumenta o reduce el tamaño de texto para mayor comodidad de lectura."
    )
    
    # ===== CONFIGURACIÓN DE OPTIMIZACIÓN =====
    unidad_medida_predeterminada = forms.ChoiceField(
        label="Unidad de medida predeterminada",
        choices=[
            ('cm', 'Centímetros (cm)'),
            ('m', 'Metros (m)'),
            ('mm', 'Milímetros (mm)'),
            ('in', 'Pulgadas (in)'),
            ('ft', 'Pies (ft)'),
        ],
        required=True,
        help_text="Unidad de medida que se usará por defecto en nuevas optimizaciones",
        widget=forms.Select(attrs={'class': 'form-control', 'data-pref-key': 'unidad_medida_predeterminada'})
    )
    
    algoritmo_predeterminado = forms.ChoiceField(
        label="Algoritmo de optimización predeterminado",
        choices=[
            ('ffd', 'First Fit Decreasing (FFD)'),
            ('best_fit', 'Best Fit'),
            ('first_fit', 'First Fit'),
        ],
        required=True,
        help_text="Algoritmo que se usará por defecto (actualmente solo FFD está implementado)",
        widget=forms.Select(attrs={'class': 'form-control', 'data-pref-key': 'algoritmo_predeterminado'})
    )
    
    margen_corte_predeterminado = forms.DecimalField(
        label="Margen de corte predeterminado (mm)",
        required=False,  # Cambiado a False para poder detectar cuando está vacío
        min_value=Decimal('0.0'),
        max_value=Decimal('10.0'),
        initial=Decimal('3.0'),  # 3 mm (equivalente a 0.3 cm)
        help_text="Grosor de la hoja de sierra en milímetros (típicamente 2-4 mm)",
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0',
            'max': '10'
        })
    )
    
    rotacion_automatica_predeterminada = forms.BooleanField(
        label="Permitir rotación automática por defecto",
        required=False,
        help_text="Las piezas se podrán rotar automáticamente para optimizar el espacio",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    # ===== CONFIGURACIÓN DE NOTIFICACIONES =====
    notificaciones_email = forms.BooleanField(
        label="Notificaciones por Email",
        required=False,
        help_text="Recibir notificaciones por correo electrónico",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    notificaciones_pantalla = forms.BooleanField(
        label="Notificaciones en Pantalla",
        required=False,
        help_text="Mostrar notificaciones en pantalla",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    email_notificaciones = forms.EmailField(
        label="Email para Notificaciones",
        required=False,
        help_text="Email para recibir notificaciones (opcional, por defecto se usa el email del usuario)",
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    
    notificar_optimizacion_completada = forms.BooleanField(
        label="Optimización Completada",
        required=False,
        help_text="Notificar cuando se completa una optimización",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    notificar_presupuesto_creado = forms.BooleanField(
        label="Presupuesto Creado",
        required=False,
        help_text="Notificar cuando se crea un presupuesto",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    notificar_proyecto_creado = forms.BooleanField(
        label="Proyecto Creado",
        required=False,
        help_text="Notificar cuando se crea un proyecto",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    notificar_errores = forms.BooleanField(
        label="Errores en Optimización",
        required=False,
        help_text="Notificar cuando hay errores en la optimización",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = PerfilUsuario
        fields = [
            'timeout_sesion', 
            'tema_preferido',
            'unidad_medida_predeterminada',
            'algoritmo_predeterminado',
            # 'margen_corte_predeterminado' - EXCLUIDO: se maneja completamente manualmente
            'rotacion_automatica_predeterminada',
            'notificaciones_email',
            'notificaciones_pantalla',
            'email_notificaciones',
            'notificar_optimizacion_completada',
            'notificar_presupuesto_creado',
            'notificar_proyecto_creado',
            'notificar_errores',
        ]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        instance = kwargs.get('instance', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            # Inicializar campos del User
            self.fields['username'].initial = self.user.username
            self.fields['email'].initial = self.user.email
            
            # CORREGIDO: Inicializar campos desde la instancia SIEMPRE, no solo cuando hay datos POST
            # Esto asegura que los valores guardados se muestren correctamente al recargar la página
            if instance:
                # Refrescar la instancia desde la BD para obtener los valores más recientes
                instance.refresh_from_db()
                
                # Campos de la pestaña de información personal
                # Siempre establecer initial, incluso si es None (para campos opcionales)
                self.fields['timeout_sesion'].initial = instance.timeout_sesion
                # Tema preferido siempre tiene un valor (default='auto'), así que siempre establecerlo
                self.fields['tema_preferido'].initial = instance.tema_preferido
                
                # Unidad de medida predeterminada - siempre tiene un valor (default='cm')
                # Normalizar 'pulgadas' a 'in' si existe en datos antiguos
                unidad = instance.unidad_medida_predeterminada
                if unidad == 'pulgadas':
                    unidad = 'in'
                self.fields['unidad_medida_predeterminada'].initial = unidad
                
                # Algoritmo predeterminado - siempre tiene un valor (default='ffd')
                self.fields['algoritmo_predeterminado'].initial = instance.algoritmo_predeterminado
                
                # Margen de corte predeterminado - siempre tiene un valor (default=0.3 cm = 3 mm)
                # CORREGIDO: Convertir de cm (BD) a mm (formulario) para mostrar
                # El campo en BD está en cm, pero el formulario muestra en mm
                if instance.margen_corte_predeterminado is not None:
                    margen_cm = float(instance.margen_corte_predeterminado)
                    margen_mm = margen_cm * 10.0  # Convertir cm a mm
                    # Redondear a 1 decimal y asegurar que se muestre correctamente
                    margen_mm_redondeado = round(margen_mm, 1)
                    # Si el valor es un entero (ej: 4.0), mostrar como entero (4)
                    if margen_mm_redondeado == int(margen_mm_redondeado):
                        self.fields['margen_corte_predeterminado'].initial = Decimal(str(int(margen_mm_redondeado)))
                    else:
                        self.fields['margen_corte_predeterminado'].initial = Decimal(str(margen_mm_redondeado))
                
                # Rotación automática predeterminada - siempre tiene un valor (default=True)
                self.fields['rotacion_automatica_predeterminada'].initial = instance.rotacion_automatica_predeterminada
                
                # Configuración de notificaciones - siempre establecer initial para booleanos
                # Los booleanos pueden ser False, que es un valor válido, así que siempre establecerlos
                self.fields['notificaciones_email'].initial = instance.notificaciones_email
                self.fields['notificaciones_pantalla'].initial = instance.notificaciones_pantalla
                # Email de notificaciones puede ser None, pero establecerlo si existe
                self.fields['email_notificaciones'].initial = instance.email_notificaciones if instance.email_notificaciones else None
                # Los demás campos de notificación siempre tienen valores (default=True)
                self.fields['notificar_optimizacion_completada'].initial = instance.notificar_optimizacion_completada
                self.fields['notificar_presupuesto_creado'].initial = instance.notificar_presupuesto_creado
                self.fields['notificar_proyecto_creado'].initial = instance.notificar_proyecto_creado
                self.fields['notificar_errores'].initial = instance.notificar_errores
    
    def clean(self):
        """Validación general del formulario"""
        cleaned_data = super().clean()
        
        # Validar margen_corte_predeterminado manualmente (ya que no está en Meta)
        if 'margen_corte_predeterminado' in self.data:
            margen_value = self.data.get('margen_corte_predeterminado', '').strip()
            if margen_value:
                try:
                    margen_mm = Decimal(str(margen_value))
                    if margen_mm < 0:
                        self.add_error('margen_corte_predeterminado', 
                                     forms.ValidationError("El margen de corte no puede ser negativo."))
                    elif margen_mm > 10:
                        self.add_error('margen_corte_predeterminado', 
                                     forms.ValidationError("El margen de corte no puede ser mayor a 10 mm."))
                except (ValueError, TypeError):
                    self.add_error('margen_corte_predeterminado', 
                                 forms.ValidationError("El valor del margen de corte no es válido."))
        
        return cleaned_data

    def clean_username(self):
        username = self.cleaned_data.get('username')
        # Si username está vacío pero viene de la pestaña de configuración, usar el valor actual
        if not username and self.user:
            return self.user.username
        # Verificar que el nuevo username no esté en uso (si se está cambiando)
        if self.user and username and username != self.user.username:
            if User.objects.filter(username=username).exclude(pk=self.user.pk).exists():
                raise forms.ValidationError("Este nombre de usuario ya está en uso.")
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Si email está vacío pero viene de la pestaña de configuración, usar el valor actual
        if not email and self.user:
            return self.user.email
        return email
    
    def clean_timeout_sesion(self):
        """Maneja valores vacíos para timeout_sesion, convirtiéndolos a None"""
        timeout_sesion = self.cleaned_data.get('timeout_sesion')
        # Si está vacío o es una cadena vacía, retornar None
        if timeout_sesion == '' or timeout_sesion is None:
            return None
        return timeout_sesion
    
    def clean_margen_corte_predeterminado(self):
        """
        Valida el margen de corte.
        Este método se llama cuando el campo está en el formulario, pero como lo excluimos
        del Meta, este método no debería llamarse normalmente. Se mantiene por compatibilidad.
        """
        margen_mm = self.cleaned_data.get('margen_corte_predeterminado')
        
        # Validar que el valor esté en el rango correcto
        if margen_mm is not None and margen_mm != '':
            try:
                margen_mm_decimal = Decimal(str(margen_mm))
                if margen_mm_decimal < 0:
                    raise forms.ValidationError("El margen de corte no puede ser negativo.")
                if margen_mm_decimal > 10:
                    raise forms.ValidationError("El margen de corte no puede ser mayor a 10 mm.")
            except (ValueError, TypeError):
                raise forms.ValidationError("El valor del margen de corte no es válido.")
        
        return margen_mm
    
    def save(self, commit=True):
        # Guardar los valores originales ANTES de que super().save() los modifique
        valor_original_cm = None
        valor_original_unidad = None
        if self.instance and self.instance.pk:
            self.instance.refresh_from_db()
            valor_original_cm = self.instance.margen_corte_predeterminado
            valor_original_unidad = self.instance.unidad_medida_predeterminada
        
        # Guardar el valor del POST directamente (en mm) antes de que Django lo procese
        # Como el campo está excluido del Meta, necesitamos obtenerlo del data del formulario
        margen_mm_post = None
        if self.data and 'margen_corte_predeterminado' in self.data:
            margen_value = self.data.get('margen_corte_predeterminado', '').strip()
            if margen_value:
                try:
                    margen_mm_post = Decimal(str(margen_value))
                except (ValueError, TypeError):
                    margen_mm_post = None
        
        # Guardar el valor de unidad de medida del POST directamente
        unidad_post = None
        if self.data and 'unidad_medida_predeterminada' in self.data:
            unidad_value = self.data.get('unidad_medida_predeterminada', '').strip()
            if unidad_value:
                # Normalizar 'pulgadas' a 'in' si existe en datos antiguos
                if unidad_value == 'pulgadas':
                    unidad_value = 'in'
                unidad_post = unidad_value
        
        perfil = super().save(commit=False)
        
        # CRÍTICO: Manejar margen_corte_predeterminado manualmente
        # Como el campo está excluido del Meta, Django NO lo procesará automáticamente
        # así que tenemos control total sobre él
        
        if margen_mm_post is not None:
            try:
                # Si hay una instancia existente, comparar con el valor original
                if valor_original_cm is not None:
                    # Convertir el valor original (en cm) a mm para comparar
                    valor_original_mm = Decimal(str(valor_original_cm)) * Decimal('10.0')
                    # Redondear para comparación (usar 1 decimal)
                    valor_original_mm_redondeado = round(valor_original_mm, 1)
                    margen_mm_redondeado = round(margen_mm_post, 1)
                    
                    # Si los valores son iguales, el usuario no modificó el campo
                    # Preservar el valor original (en cm) sin convertir
                    if valor_original_mm_redondeado == margen_mm_redondeado:
                        # Restaurar el valor original en cm (no convertir)
                        perfil.margen_corte_predeterminado = valor_original_cm
                    else:
                        # El valor cambió, convertir de mm a cm
                        margen_cm = margen_mm_post / Decimal('10.0')
                        perfil.margen_corte_predeterminado = round(margen_cm, 2)
                else:
                    # No hay valor original, convertir de mm a cm
                    margen_cm = margen_mm_post / Decimal('10.0')
                    perfil.margen_corte_predeterminado = round(margen_cm, 2)
            except (ValueError, TypeError):
                # Si hay error, preservar el valor original si existe
                if valor_original_cm is not None:
                    perfil.margen_corte_predeterminado = valor_original_cm
        else:
            # Si el campo está vacío o no se proporcionó, preservar el valor original si existe
            if valor_original_cm is not None:
                perfil.margen_corte_predeterminado = valor_original_cm
        
        # CRÍTICO: Manejar unidad_medida_predeterminada manualmente
        # Asegurarnos de que el valor del POST se guarde correctamente
        # Obtener también el valor de cleaned_data por si acaso (Django lo procesa automáticamente)
        unidad_cleaned = self.cleaned_data.get('unidad_medida_predeterminada')
        
        # Priorizar el valor del POST directo, pero si no está, usar cleaned_data
        unidad_final = unidad_post if unidad_post is not None else unidad_cleaned
        
        if unidad_final is not None:
            # Normalizar 'pulgadas' a 'in' si existe
            if unidad_final == 'pulgadas':
                unidad_final = 'in'
            # Verificar que la unidad esté en las opciones válidas
            unidades_validas = [choice[0] for choice in self.fields['unidad_medida_predeterminada'].choices]
            if unidad_final in unidades_validas:
                # SIEMPRE asignar el valor del POST/cleaned_data, incluso si es igual al original
                # Esto asegura que el valor se guarde correctamente
                perfil.unidad_medida_predeterminada = unidad_final
            # Si no está en las opciones válidas, preservar el valor original
            elif valor_original_unidad is not None:
                perfil.unidad_medida_predeterminada = valor_original_unidad
        else:
            # Si el campo está vacío o no se proporcionó, preservar el valor original si existe
            if valor_original_unidad is not None:
                perfil.unidad_medida_predeterminada = valor_original_unidad
        
        if commit:
            # Actualizar datos del User solo si se proporcionaron
            if self.user:
                username = self.cleaned_data.get('username')
                email = self.cleaned_data.get('email')
                if username:
                    self.user.username = username
                if email:
                    self.user.email = email
                self.user.save()
            perfil.save()
        return perfil

class CambiarPasswordForm(PasswordChangeForm):
    """Formulario para cambiar contraseña"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Mejorar estilos de los campos
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})
