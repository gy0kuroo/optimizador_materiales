from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from .forms import RegistroForm, PerfilForm, CambiarPasswordForm
from .models import PerfilUsuario

def registro(request):
    if request.method == "POST":
        form = RegistroForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Cuenta creada exitosamente! Por favor inicia sesión.')
            return redirect('usuarios:login')
    else:
        form = RegistroForm()
    return render(request, 'usuarios/registro.html', {'form': form})


def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            # Asegurar que el usuario tenga un perfil
            perfil, created = PerfilUsuario.objects.get_or_create(usuario=user)
            # Guardar timeout personalizado en la sesión si existe y no está desactivado
            if perfil.timeout_sesion is not None and perfil.timeout_sesion != 0:
                timeout_segundos = perfil.get_timeout_segundos()
                if timeout_segundos:
                    request.session['timeout_personalizado'] = timeout_segundos
            elif perfil.timeout_sesion == 0:
                # Si está desactivado, limpiar cualquier timeout previo
                request.session.pop('timeout_personalizado', None)
            return redirect('opticut:index')  #la entrada al usuario va con separacion de :, el nombre de opticut quedó como "index
    else:
        form = AuthenticationForm()
    return render(request, 'usuarios/login.html', {'form': form})

def logout_view(request):
    logout(request)
    request.session.flush()
    return redirect('usuarios:login')

@login_required
def perfil(request):
    """Vista para ver y editar el perfil del usuario"""
    try:
        perfil = request.user.perfil
    except PerfilUsuario.DoesNotExist:
        # Si no existe, crearlo
        perfil = PerfilUsuario.objects.create(usuario=request.user)
    
    perfil_form = PerfilForm(instance=perfil, user=request.user)
    password_form = CambiarPasswordForm(user=request.user)
    
    if request.method == "POST":
        if 'editar_perfil' in request.POST:
            perfil_form = PerfilForm(request.POST, instance=perfil, user=request.user)
            if perfil_form.is_valid():
                perfil_form.save()
                # Actualizar timeout en sesión
                perfil.refresh_from_db()  # Recargar para obtener los valores actualizados
                if perfil.timeout_sesion is not None and perfil.timeout_sesion != 0:
                    request.session['timeout_personalizado'] = perfil.get_timeout_segundos()
                else:
                    request.session.pop('timeout_personalizado', None)
                # Guardar tema preferido en sesión y localStorage (se aplicará con JavaScript)
                if perfil.tema_preferido != 'auto':
                    request.session['tema_preferido'] = perfil.tema_preferido
                else:
                    request.session.pop('tema_preferido', None)
                messages.success(request, 'Perfil actualizado exitosamente.')
                return redirect('usuarios:perfil')
        
        elif 'cambiar_password' in request.POST:
            password_form = CambiarPasswordForm(user=request.user, data=request.POST)
            if password_form.is_valid():
                password_form.save()
                update_session_auth_hash(request, password_form.user)
                messages.success(request, 'Contraseña cambiada exitosamente.')
                return redirect('usuarios:perfil')
    
    return render(request, 'usuarios/perfil.html', {
        'perfil_form': perfil_form,
        'password_form': password_form,
        'perfil': perfil
    })
