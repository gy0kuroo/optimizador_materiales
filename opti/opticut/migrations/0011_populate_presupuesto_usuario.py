# Generated migration to populate usuario field in Presupuesto

from django.db import migrations

def populate_usuario_from_optimizaciones(apps, schema_editor):
    """
    Asigna el usuario a cada presupuesto basándose en las optimizaciones asociadas.
    Si un presupuesto tiene optimizaciones, usa el usuario de la primera optimización.
    """
    Presupuesto = apps.get_model('opticut', 'Presupuesto')
    Optimizacion = apps.get_model('opticut', 'Optimizacion')
    
    for presupuesto in Presupuesto.objects.filter(usuario__isnull=True):
        # Obtener la primera optimización asociada
        optimizacion = presupuesto.optimizaciones.first()
        if optimizacion:
            presupuesto.usuario = optimizacion.usuario
            presupuesto.save()
        else:
            # Si no hay optimizaciones, intentar obtener el usuario del cliente
            if presupuesto.cliente:
                presupuesto.usuario = presupuesto.cliente.usuario
                presupuesto.save()
            elif presupuesto.proyecto:
                presupuesto.usuario = presupuesto.proyecto.usuario
                presupuesto.save()

def reverse_populate_usuario(apps, schema_editor):
    """Operación reversa: no hace nada"""
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('opticut', '0010_add_usuario_to_presupuesto'),
    ]

    operations = [
        migrations.RunPython(populate_usuario_from_optimizaciones, reverse_populate_usuario),
    ]

