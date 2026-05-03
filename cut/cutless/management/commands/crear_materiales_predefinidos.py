"""
Comando de management para crear materiales predefinidos del sistema.
Basado en los tableros predefinidos del archivo medidas-pred.js
"""
from django.core.management.base import BaseCommand
from cutless.models import Material

class Command(BaseCommand):
    help = 'Crea los materiales predefinidos del sistema basados en tableros estándar'

    def handle(self, *args, **options):
        # Materiales predefinidos basados en medidas-pred.js
        materiales_predefinidos = [
            {
                'nombre': 'OSB',
                'ancho': 122,
                'alto': 244,
                'unidad_medida': 'cm',
                'descripcion': 'Tablero OSB estándar 122×244 cm'
            },
            {
                'nombre': 'MDF',
                'ancho': 122,
                'alto': 244,
                'unidad_medida': 'cm',
                'descripcion': 'Tablero MDF estándar 122×244 cm'
            },
            {
                'nombre': 'MDF',
                'ancho': 183,
                'alto': 244,
                'unidad_medida': 'cm',
                'descripcion': 'Tablero MDF estándar 183×244 cm'
            },
            {
                'nombre': 'Melamina',
                'ancho': 183,
                'alto': 244,
                'unidad_medida': 'cm',
                'descripcion': 'Tablero de Melamina estándar 183×244 cm'
            },
            {
                'nombre': 'Contrachapado',
                'ancho': 122,
                'alto': 244,
                'unidad_medida': 'cm',
                'descripcion': 'Tablero de Contrachapado estándar 122×244 cm'
            },
            {
                'nombre': 'Tablero',
                'ancho': 152,
                'alto': 244,
                'unidad_medida': 'cm',
                'descripcion': 'Tablero estándar 152×244 cm'
            },
        ]
        
        creados = 0
        actualizados = 0
        
        for mat_data in materiales_predefinidos:
            # Buscar si ya existe un material predefinido con estas dimensiones y nombre
            material, created = Material.objects.get_or_create(
                es_predefinido=True,
                nombre=mat_data['nombre'],
                ancho=mat_data['ancho'],
                alto=mat_data['alto'],
                defaults={
                    'unidad_medida': mat_data['unidad_medida'],
                    'descripcion': mat_data['descripcion'],
                    'usuario': None,  # Materiales predefinidos no tienen usuario
                }
            )
            
            if created:
                creados += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'[OK] Creado: {material.nombre} ({material.ancho}x{material.alto} cm)'
                    )
                )
            else:
                # Actualizar descripción si cambió
                if material.descripcion != mat_data['descripcion']:
                    material.descripcion = mat_data['descripcion']
                    material.save()
                    actualizados += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f'[ACTUALIZADO] {material.nombre} ({material.ancho}x{material.alto} cm)'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.NOTICE(
                            f'[YA EXISTE] {material.nombre} ({material.ancho}x{material.alto} cm)'
                        )
                    )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nProceso completado: {creados} creados, {actualizados} actualizados'
            )
        )

