from .models import Optimizacion

def tutorial_context(request):
    """
    Context processor para agregar información del tutorial a todas las plantillas.
    """
    if request.user.is_authenticated:
        tiene_optimizaciones = Optimizacion.objects.filter(usuario=request.user).exists()
        # Una sola vez tras login exitoso (sesión); evita el modal en la pantalla de login u otras rutas
        mostrar_modal = request.session.pop('mostrar_bienvenida_cutless', False)
        return {
            'tiene_optimizaciones': tiene_optimizaciones,
            'mostrar_modal_bienvenida': mostrar_modal,
        }
    return {
        'tiene_optimizaciones': False,
        'mostrar_modal_bienvenida': False,
    }

