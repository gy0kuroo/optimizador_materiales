from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.urls import reverse
from .forms import RegistroForm, PerfilForm, UsuarioEdicionForm, PermisosUsuarioForm, CambiarPasswordForm
from .models import PerfilUsuario

def registro(request):
    if request.method == "POST":
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Asegurar la existencia de perfil
            PerfilUsuario.objects.get_or_create(usuario=user)
            messages.success(request, '¡Cuenta creada exitosamente! Por favor inicia sesión.')
            return redirect('usuarios:login')
    else:
        form = RegistroForm()
    return render(request, 'usuarios/registro.html', {'form': form})


def es_admin(usuario):
    if not usuario.is_authenticated:
        return False
    if usuario.is_superuser:
        return True
    try:
        return usuario.perfil.rol == 'admin'
    except PerfilUsuario.DoesNotExist:
        return False


@login_required
@user_passes_test(es_admin)
def admin_dashboard(request):
    usuarios = User.objects.all().order_by('username')

    if request.method == 'POST' and 'crear_usuario' in request.POST:
        form = RegistroForm(request.POST)
        rol = request.POST.get('rol', 'usuario')
        if form.is_valid():
            user = form.save(commit=False)
            user.is_staff = (rol == 'admin')
            user.save()
            perfil, creado = PerfilUsuario.objects.get_or_create(usuario=user)
            if not creado:
                perfil.rol = rol
            else:
                perfil.rol = rol
            perfil.save()
            messages.success(request, f"Usuario '{user.username}' creado con rol '{rol}'.")
            return redirect('usuarios:admin_dashboard')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario de creación.')
    else:
        form = RegistroForm()

    return render(request, 'usuarios/admin_dashboard.html', {
        'usuarios': usuarios,
        'form': form
    })


@login_required
@user_passes_test(es_admin)
def eliminar_usuario(request, pk):
    usuario = get_object_or_404(User, pk=pk)
    if usuario == request.user:
        messages.error(request, 'No puedes eliminar tu propia cuenta desde aquí.')
        return redirect('usuarios:admin_dashboard')

    usuario.delete()
    messages.success(request, f"Usuario {usuario.username} eliminado.")
    return redirect('usuarios:admin_dashboard')


@login_required
@user_passes_test(es_admin)
def editar_usuario(request, pk):
    usuario = get_object_or_404(User, pk=pk)
    
    # Obtener o crear el perfil del usuario
    try:
        perfil = usuario.perfil
    except PerfilUsuario.DoesNotExist:
        perfil = PerfilUsuario.objects.create(usuario=usuario)

    if request.method == 'POST':
        form = UsuarioEdicionForm(request.POST, instance=usuario)
        permisos_form = PermisosUsuarioForm(request.POST, instance=perfil)
        
        if form.is_valid() and permisos_form.is_valid():
            form.save()
            permisos_form.save()
            password = form.cleaned_data.get('password1')
            if password:
                usuario.set_password(password)
                usuario.save()
            messages.success(request, f"Usuario '{usuario.username}' actualizado correctamente.")
            return redirect('usuarios:admin_dashboard')
        else:
            messages.error(request, 'Por favor corrige los errores del formulario.')
    else:
        form = UsuarioEdicionForm(instance=usuario)
        permisos_form = PermisosUsuarioForm(instance=perfil)

    return render(request, 'usuarios/editar_usuario.html', {
        'usuario_obj': usuario,
        'form': form,
        'permisos_form': permisos_form,
        'perfil': perfil,
    })


@login_required
@user_passes_test(es_admin)
def actualizar_rol(request, pk):
    if request.method == 'POST':
        usuario = get_object_or_404(User, pk=pk)
        rol = request.POST.get('rol', 'usuario')
        perfil, _ = PerfilUsuario.objects.get_or_create(usuario=usuario)
        perfil.rol = rol
        perfil.save()
        if rol == 'admin':
            usuario.is_staff = True
        else:
            usuario.is_staff = False
        usuario.save()
        messages.success(request, f"Rol del usuario {usuario.username} actualizado a {rol}.")
    return redirect('usuarios:admin_dashboard')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('cutless:index')
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            # Asegurar que el usuario tenga un perfil
            perfil, created = PerfilUsuario.objects.get_or_create(usuario=user)
            # Configurar timeout de sesión según el perfil del usuario
            if perfil.timeout_sesion is not None and perfil.timeout_sesion != 0:
                timeout_segundos = perfil.get_timeout_segundos()
                if timeout_segundos:
                    request.session['timeout_personalizado'] = timeout_segundos
                    # Configurar expiración de sesión en Django (en segundos)
                    request.session.set_expiry(timeout_segundos)
            elif perfil.timeout_sesion == 0:
                # Si está desactivado (0), configurar sesión para que no expire nunca
                # Usar un valor muy grande (10 años en segundos) para simular "sin expiración"
                request.session.pop('timeout_personalizado', None)
                request.session.set_expiry(315360000)  # 10 años en segundos (prácticamente sin expiración)
            else:
                # Si es None, usar el valor por defecto del sistema
                request.session.pop('timeout_personalizado', None)
                request.session.set_expiry(None)  # Usar SESSION_COOKIE_AGE por defecto
            # Mostrar modal de bienvenida solo en la primera vista tras login exitoso
            request.session['mostrar_bienvenida_cutless'] = True
            return redirect('cutless:index')
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
    
    # CORREGIDO: Refrescar el perfil desde la BD antes de inicializar el formulario
    # Esto asegura que siempre tengamos los valores más recientes
    perfil.refresh_from_db()
    
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
                    timeout_segundos = perfil.get_timeout_segundos()
                    if timeout_segundos:
                        request.session['timeout_personalizado'] = timeout_segundos
                        # Configurar expiración de sesión en Django (en segundos)
                        request.session.set_expiry(timeout_segundos)
                elif perfil.timeout_sesion == 0:
                    # Si está desactivado (0), configurar sesión para que no expire nunca
                    request.session.pop('timeout_personalizado', None)
                    request.session.set_expiry(315360000)  # 10 años en segundos (prácticamente sin expiración)
                else:
                    # Si es None, usar el valor por defecto del sistema
                    request.session.pop('timeout_personalizado', None)
                    request.session.set_expiry(None)  # Usar SESSION_COOKIE_AGE por defecto
                # Guardar tema preferido en sesión y localStorage (se aplicará con JavaScript)
                if perfil.tema_preferido != 'auto':
                    request.session['tema_preferido'] = perfil.tema_preferido
                else:
                    request.session.pop('tema_preferido', None)

                # Guardar otras preferencias en sesión para consistencia (también en JS localStorage)
                request.session['unidad_medida_predeterminada'] = perfil.unidad_medida_predeterminada
                request.session['algoritmo_predeterminado'] = perfil.algoritmo_predeterminado
                request.session['tamanio_fuente'] = perfil.tamanio_fuente

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


@login_required
def configuracion_sistema(request):
    """Vista para editar solo la configuración del sistema (valores predeterminados)"""
    try:
        perfil = request.user.perfil
    except PerfilUsuario.DoesNotExist:
        perfil = PerfilUsuario.objects.create(usuario=request.user)
    
    perfil.refresh_from_db()
    
    # Crear formulario solo con campos de configuración del sistema
    perfil_form = PerfilForm(instance=perfil, user=request.user)
    permisos_form = PermisosUsuarioForm(instance=perfil)
    password_form = CambiarPasswordForm(user=request.user)  # Necesario para el template
    mostrar_tab_funcionalidades = False
    
    if request.method == "POST":
        if 'editar_permisos_menu' in request.POST:
            permisos_form = PermisosUsuarioForm(request.POST, instance=perfil)
            if permisos_form.is_valid():
                permisos_form.save()
                messages.success(
                    request,
                    'Funcionalidades del sistema actualizadas. Los cambios se aplican de inmediato.',
                )
                url = reverse('usuarios:configuracion_sistema') + '?tab=funcionalidades'
                return redirect(url)
            messages.error(request, 'Por favor corrige los errores en funcionalidades del sistema.')
            mostrar_tab_funcionalidades = True
        elif 'editar_configuracion' in request.POST:
            post_data = request.POST.copy()
            perfil.refresh_from_db()



            # Asegurar que los campos ocultos tengan valores válidos
            if not post_data.get('timeout_sesion') or post_data.get('timeout_sesion') == '':
                if perfil.timeout_sesion is not None:
                    post_data['timeout_sesion'] = str(perfil.timeout_sesion)
                else:
                    if 'timeout_sesion' in post_data:
                        del post_data['timeout_sesion']

            if not post_data.get('tema_preferido') or post_data.get('tema_preferido') == '':
                post_data['tema_preferido'] = perfil.tema_preferido if perfil.tema_preferido else 'auto'

            # Asegurar campos de información personal
            if not post_data.get('username'):
                post_data['username'] = request.user.username
            if not post_data.get('email'):
                post_data['email'] = request.user.email

            perfil_form = PerfilForm(post_data, instance=perfil, user=request.user)
            if perfil_form.is_valid():
                perfil_form.save()
                perfil.refresh_from_db()

                # Sincronizar preferencias de configuración de sistema a sesión
                request.session['unidad_medida_predeterminada'] = perfil.unidad_medida_predeterminada
                request.session['algoritmo_predeterminado'] = perfil.algoritmo_predeterminado
                request.session['tamanio_fuente'] = perfil.tamanio_fuente
                request.session['tema_preferido'] = perfil.tema_preferido

                messages.success(request, 'Configuración del sistema actualizada exitosamente.')
                return redirect('usuarios:configuracion_sistema')
            else:
                messages.error(request, 'Por favor corrige los errores en el formulario.')
                if settings.DEBUG:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Errores del formulario: {perfil_form.errors}")
                    print(f"Errores del formulario: {perfil_form.errors}")
    
    return render(request, 'usuarios/configuracion_sistema.html', {
        'perfil_form': perfil_form,
        'permisos_form': permisos_form,
        'password_form': password_form,
        'perfil': perfil,
        'mostrar_tab_funcionalidades': mostrar_tab_funcionalidades,
    })


@login_required
def completar_tutorial(request):
    """
    Marca el tutorial como completado para el usuario actual.
    """
    try:
        perfil = request.user.perfil
        perfil.tutorial_completado = True
        perfil.save()
        return JsonResponse({'success': True, 'message': 'Tutorial marcado como completado'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


def recuperar_password(request):
    """
    Vista para solicitar recuperación de contraseña.
    """
    if request.method == "POST":
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                # Generar token
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                
                # Crear URL de reset
                reset_url = request.build_absolute_uri(
                    f'/usuarios/reset-password/{uid}/{token}/'
                )
                
                # Enviar email
                subject = 'Recuperación de contraseña - CutLess'
                message = render_to_string('usuarios/email_reset_password.html', {
                    'user': user,
                    'reset_url': reset_url,
                    'site_name': 'CutLess'
                })
                
                # Intentar enviar email
                try:
                    send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@CutLess.com',
                        [email],
                        html_message=message,
                        fail_silently=False,
                    )
                    messages.success(
                        request, 
                        'Se ha enviado un correo electrónico con las instrucciones para recuperar tu contraseña. '
                        'Por favor revisa tu bandeja de entrada.'
                    )
                except Exception as e:
                    # Si no hay configuración de email, mostrar el link directamente (solo en desarrollo)
                    if settings.DEBUG:
                        messages.warning(
                            request,
                            f'⚠️ Configuración de email no disponible. En producción, configura SMTP. '
                            f'Link de reset: {reset_url}'
                        )
                    else:
                        messages.error(
                            request,
                            'Error al enviar el correo. Por favor contacta al administrador.'
                        )
                
                return redirect('usuarios:login')
            except User.DoesNotExist:
                # Por seguridad, no revelar si el email existe o no
                messages.success(
                    request,
                    'Si el correo existe en nuestro sistema, recibirás las instrucciones para recuperar tu contraseña.'
                )
                return redirect('usuarios:login')
    else:
        form = PasswordResetForm()
    
    return render(request, 'usuarios/recuperar_password.html', {'form': form})


def reset_password_confirm(request, uidb64, token):
    """
    Vista para confirmar y establecer nueva contraseña.
    """
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        if request.method == "POST":
            form = SetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Tu contraseña ha sido restablecida exitosamente. Puedes iniciar sesión ahora.')
                return redirect('usuarios:login')
        else:
            form = SetPasswordForm(user)
        
        return render(request, 'usuarios/reset_password_confirm.html', {'form': form})
    else:
        messages.error(request, 'El enlace de recuperación no es válido o ha expirado. Por favor solicita uno nuevo.')
        return redirect('usuarios:recuperar_password')