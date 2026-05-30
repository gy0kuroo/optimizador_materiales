"""Notificaciones en pantalla y por email segun preferencias del usuario."""

from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.template.loader import render_to_string


def enviar_notificacion(request, tipo, titulo, mensaje, contexto_adicional=None):
    """
    Envia una notificacion al usuario segun sus preferencias.

    Args:
        request: Objeto request de Django
        tipo: 'optimizacion_completada', 'presupuesto_creado', 'proyecto_creado', 'error'
        titulo: Titulo de la notificacion
        mensaje: Mensaje de la notificacion
        contexto_adicional: Contexto extra para el email (opcional)
    """
    if not request.user.is_authenticated:
        return

    try:
        perfil = request.user.perfil
        perfil.refresh_from_db()
    except Exception as e:
        perfil = None
        if settings.DEBUG:
            print(f"DEBUG enviar_notificacion: Error obteniendo perfil: {e}")

    if not perfil:
        messages.success(request, f"{titulo}: {mensaje}")
        if settings.DEBUG:
            print("DEBUG enviar_notificacion: No hay perfil, mostrando notificacion por defecto")
        return

    if settings.DEBUG:
        print(f"DEBUG enviar_notificacion: perfil.notificaciones_pantalla = {perfil.notificaciones_pantalla}")
        print(f"DEBUG enviar_notificacion: perfil.notificar_optimizacion_completada = {perfil.notificar_optimizacion_completada}")

    debe_notificar = False
    if tipo == 'optimizacion_completada':
        debe_notificar = perfil.notificar_optimizacion_completada
    elif tipo == 'presupuesto_creado':
        debe_notificar = perfil.notificar_presupuesto_creado
    elif tipo == 'proyecto_creado':
        debe_notificar = perfil.notificar_proyecto_creado
    elif tipo == 'error':
        debe_notificar = perfil.notificar_errores
    else:
        debe_notificar = True

    if settings.DEBUG:
        print(f"DEBUG enviar_notificacion: tipo={tipo}, debe_notificar={debe_notificar}")

    if not debe_notificar:
        if settings.DEBUG:
            print("DEBUG enviar_notificacion: No se debe notificar este tipo de evento")
        return

    if perfil.notificaciones_pantalla:
        if tipo == 'error':
            messages.error(request, f"{titulo}: {mensaje}")
        else:
            messages.success(request, f"{titulo}: {mensaje}")
        if settings.DEBUG:
            print("DEBUG enviar_notificacion: Notificacion en pantalla enviada")
    elif settings.DEBUG:
        print("DEBUG enviar_notificacion: notificaciones_pantalla desactivado")

    if perfil.notificaciones_email:
        email_destino = perfil.email_notificaciones or request.user.email
        if email_destino:
            try:
                contexto = {
                    'usuario': request.user,
                    'titulo': titulo,
                    'mensaje': mensaje,
                    'tipo': tipo,
                }
                if contexto_adicional:
                    contexto.update(contexto_adicional)

                asunto = f"CutLess - {titulo}"
                mensaje_email = render_to_string('cutless/emails/notificacion.txt', contexto)
                mensaje_email_html = render_to_string('cutless/emails/notificacion.html', contexto)

                if hasattr(settings, 'EMAIL_HOST') and settings.EMAIL_HOST:
                    send_mail(
                        subject=asunto,
                        message=mensaje_email,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[email_destino],
                        html_message=mensaje_email_html,
                        fail_silently=True,
                    )
            except Exception:
                pass
