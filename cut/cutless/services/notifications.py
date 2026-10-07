"""Notificaciones por canal y tipo según preferencias personales."""
import logging

from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def enviar_notificacion(request, tipo, titulo, mensaje, contexto_adicional=None, *, mostrar_en_pantalla=True):
    if not request.user.is_authenticated:
        return
    try:
        perfil = request.user.perfil
        perfil.refresh_from_db()
    except Exception:
        logger.exception('No se pudo cargar el perfil para notificaciones.')
        if mostrar_en_pantalla:
            (messages.error if tipo == 'error' else messages.success)(request, f'{titulo}: {mensaje}')
        return

    evento = {
        'optimizacion_completada': 'notificar_optimizacion_completada',
        'presupuesto_creado': 'notificar_presupuesto_creado',
        'proyecto_creado': 'notificar_proyecto_creado',
        'error': 'notificar_errores',
    }.get(tipo)
    if evento and not getattr(perfil, evento):
        return
    if mostrar_en_pantalla and perfil.notificaciones_pantalla:
        (messages.error if tipo == 'error' else messages.success)(request, f'{titulo}: {mensaje}')
    if not perfil.notificaciones_email:
        return
    email_destino = perfil.email_notificaciones or request.user.email
    if not email_destino:
        logger.warning('Aviso por correo omitido: la cuenta no tiene destinatario configurado.')
        return
    try:
        contexto = {'usuario': request.user, 'titulo': titulo, 'mensaje': mensaje, 'tipo': tipo}
        if contexto_adicional:
            contexto.update(contexto_adicional)
        enviados = send_mail(
            subject=f'CutLess - {titulo}',
            message=render_to_string('cutless/emails/notificacion.txt', contexto),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email_destino],
            html_message=render_to_string('cutless/emails/notificacion.html', contexto),
            fail_silently=False,
        )
        if enviados == 0:
            logger.warning('El backend de correo no aceptó el aviso de tipo %s.', tipo)
    except Exception:
        # Un fallo del aviso no debe invalidar una operación ya realizada.
        logger.exception('No se pudo enviar el aviso por correo de tipo %s.', tipo)
