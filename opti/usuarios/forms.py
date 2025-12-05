from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from .models import PerfilUsuario

class RegistroForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class PerfilForm(forms.ModelForm):
    """Formulario para editar información del perfil"""
    username = forms.CharField(
        label="Nombre de usuario",
        max_length=150,
        required=True,
        help_text="Requerido. 150 caracteres o menos. Únicamente letras, dígitos y @/./+/-/_",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        label="Correo electrónico",
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    timeout_sesion = forms.IntegerField(
        label="Timeout de sesión (minutos)",
        required=False,
        min_value=0,
        max_value=480,  # Máximo 8 horas
        help_text="Tiempo de inactividad antes de cerrar sesión automáticamente. 0 para desactivar. Déjalo vacío para usar 30 minutos por defecto.",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '480', 'step': '5'})
    )
    tema_preferido = forms.ChoiceField(
        label="Tema preferido",
        choices=[('light', 'Claro'), ('dark', 'Oscuro'), ('auto', 'Automático')],
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = PerfilUsuario
        fields = ['timeout_sesion', 'tema_preferido']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            # Inicializar campos del User
            self.fields['username'].initial = self.user.username
            self.fields['email'].initial = self.user.email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if self.user and username != self.user.username:
            # Verificar que el nuevo username no esté en uso
            if User.objects.filter(username=username).exclude(pk=self.user.pk).exists():
                raise forms.ValidationError("Este nombre de usuario ya está en uso.")
        return username

    def save(self, commit=True):
        perfil = super().save(commit=False)
        if commit:
            # Actualizar datos del User
            if self.user:
                self.user.username = self.cleaned_data['username']
                self.user.email = self.cleaned_data['email']
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
