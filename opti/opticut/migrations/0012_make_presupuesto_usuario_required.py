# Generated migration to make usuario field required in Presupuesto

from django.db import migrations, models
import django.db.models.deletion

def ensure_all_presupuestos_have_usuario(apps, schema_editor):
    """
    Asegura que todos los presupuestos tengan un usuario asignado.
    Si algún presupuesto no tiene usuario, se elimina (no debería pasar después de la migración anterior).
    """
    Presupuesto = apps.get_model('opticut', 'Presupuesto')
    
    # Eliminar presupuestos sin usuario (no debería haber ninguno)
    presupuestos_sin_usuario = Presupuesto.objects.filter(usuario__isnull=True)
    count = presupuestos_sin_usuario.count()
    if count > 0:
        print(f"Advertencia: Se encontraron {count} presupuestos sin usuario. Se eliminarán.")
        presupuestos_sin_usuario.delete()

class Migration(migrations.Migration):

    dependencies = [
        ('opticut', '0011_populate_presupuesto_usuario'),
    ]

    operations = [
        migrations.RunPython(ensure_all_presupuestos_have_usuario, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='presupuesto',
            name='usuario',
            field=models.ForeignKey(
                help_text='Usuario propietario del presupuesto',
                on_delete=django.db.models.deletion.CASCADE,
                to='auth.User'
            ),
        ),
    ]

