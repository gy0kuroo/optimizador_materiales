"""
Utilidades para el sistema de notificaciones
"""
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string


def enviar_notificacion(request, tipo, titulo, mensaje, contexto_adicional=None):
    """
    Envía una notificación al usuario según sus preferencias.
    
    Args:
        request: Objeto request de Django
        tipo: Tipo de notificación ('optimizacion_completada', 'presupuesto_creado', 'proyecto_creado', 'error')
        titulo: Título de la notificación
        mensaje: Mensaje de la notificación
        contexto_adicional: Diccionario con contexto adicional para el email (opcional)
    """
    if not request.user.is_authenticated:
        return
    
    try:
        perfil = request.user.perfil
        # CRÍTICO: Refrescar el perfil desde la BD para obtener los valores más recientes
        # Esto asegura que los cambios en la configuración de notificaciones se apliquen inmediatamente
        perfil.refresh_from_db()
    except Exception as e:
        # Si no tiene perfil, usar valores por defecto
        perfil = None
        if settings.DEBUG:
            print(f"DEBUG enviar_notificacion: Error obteniendo perfil: {e}")
    
    if not perfil:
        # Si no hay perfil, solo mostrar notificación en pantalla (comportamiento por defecto)
        messages.success(request, f"{titulo}: {mensaje}")
        if settings.DEBUG:
            print(f"DEBUG enviar_notificacion: No hay perfil, mostrando notificación por defecto")
        return
    
    # DEBUG: Verificar valores del perfil
    if settings.DEBUG:
        print(f"DEBUG enviar_notificacion: perfil.notificaciones_pantalla = {perfil.notificaciones_pantalla}")
        print(f"DEBUG enviar_notificacion: perfil.notificar_optimizacion_completada = {perfil.notificar_optimizacion_completada}")
    
    # Verificar si debe notificar este tipo de evento
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
        debe_notificar = True  # Por defecto, notificar tipos desconocidos
    
    if settings.DEBUG:
        print(f"DEBUG enviar_notificacion: tipo={tipo}, debe_notificar={debe_notificar}")
    
    if not debe_notificar:
        if settings.DEBUG:
            print(f"DEBUG enviar_notificacion: No se debe notificar este tipo de evento")
        return
    
    # Notificación en pantalla
    # CRÍTICO: Verificar notificaciones_pantalla después de refrescar desde la BD
    if perfil.notificaciones_pantalla:
        if tipo == 'error':
            messages.error(request, f"{titulo}: {mensaje}")
        else:
            messages.success(request, f"{titulo}: {mensaje}")
        if settings.DEBUG:
            print(f"DEBUG enviar_notificacion: Notificación en pantalla enviada")
    else:
        if settings.DEBUG:
            print(f"DEBUG enviar_notificacion: notificaciones_pantalla está desactivado, no se muestra mensaje")
    
    # Notificación por email
    if perfil.notificaciones_email:
        email_destino = perfil.email_notificaciones or request.user.email
        
        if email_destino:
            try:
                # Preparar contexto para el email
                contexto = {
                    'usuario': request.user,
                    'titulo': titulo,
                    'mensaje': mensaje,
                    'tipo': tipo,
                }
                if contexto_adicional:
                    contexto.update(contexto_adicional)
                
                # Renderizar el email
                asunto = f"CutLess - {titulo}"
                mensaje_email = render_to_string('cutless/emails/notificacion.txt', contexto)
                mensaje_email_html = render_to_string('cutless/emails/notificacion.html', contexto)
                
                # Enviar email (solo si está configurado en settings)
                if hasattr(settings, 'EMAIL_HOST') and settings.EMAIL_HOST:
                    send_mail(
                        subject=asunto,
                        message=mensaje_email,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[email_destino],
                        html_message=mensaje_email_html,
                        fail_silently=True,  # No fallar si hay problemas con el email
                    )
            except Exception as e:
                # Si falla el envío de email, no interrumpir el flujo
                # Solo registrar el error (en producción usar logging)
                pass

