from .models import Optimizacion

def tutorial_context(request):
    """
    Context processor para agregar información del tutorial a todas las plantillas.
    """
    if request.user.is_authenticated:
        tiene_optimizaciones = Optimizacion.objects.filter(usuario=request.user).exists()
        return {
            'tiene_optimizaciones': tiene_optimizaciones
        }
    return {
        'tiene_optimizaciones': False
    }

