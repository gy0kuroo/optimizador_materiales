import math

from django import forms

from ..models import Plantilla
from ..units import convertir_a_cm, convertir_desde_cm

class PlantillaForm(forms.ModelForm):
    """Formulario para crear y editar plantillas"""
    
    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            unidad = self.instance.unidad_medida or 'cm'
            self.initial['ancho_tablero'] = convertir_desde_cm(self.instance.ancho_tablero, unidad)
            self.initial['alto_tablero'] = convertir_desde_cm(self.instance.alto_tablero, unidad)
            self.initial['margen_corte'] = self.instance.margen_corte * 10
        else:
            self.initial.setdefault('margen_corte', 3)

    def clean(self):
        datos = super().clean()
        unidad = datos.get('unidad_medida')
        if unidad:
            for campo in ('ancho_tablero', 'alto_tablero'):
                valor = datos.get(campo)
                if valor is not None:
                    if not math.isfinite(valor) or not 10 <= convertir_a_cm(valor, unidad) <= 300:
                        self.add_error(campo, 'Cada lado del tablero debe medir entre 10 y 300 cm; revisa la unidad seleccionada.')
                    else:
                        datos[campo] = convertir_a_cm(valor, unidad)
        piezas = datos.get('piezas')
        if piezas and unidad:
            lineas = [linea for linea in piezas.splitlines() if linea.strip()]
            if len(lineas) > 20:
                self.add_error('piezas', 'Puedes guardar hasta 20 tipos de pieza.')
            for numero, linea in enumerate(lineas, 1):
                nombre_pieza, ancho, alto, cantidad = linea.split(',')
                ancho, alto = convertir_a_cm(float(ancho), unidad), convertir_a_cm(float(alto), unidad)
                if not .1 <= ancho <= 300 or not .1 <= alto <= 300:
                    self.add_error('piezas', f'Pieza {numero}: cada lado debe medir entre 0,1 y 300 cm.')
                elif datos.get('ancho_tablero') and datos.get('alto_tablero'):
                    w, h = datos['ancho_tablero'], datos['alto_tablero']
                    cabe = ancho <= w and alto <= h
                    girada = datos.get('permitir_rotacion') and alto <= w and ancho <= h
                    if not (cabe or girada):
                        self.add_error('piezas', f'Pieza {numero}: no cabe en el tablero con la rotación elegida.')
        nombre = datos.get('nombre')
        if self.user and nombre:
            existentes = Plantilla.objects.filter(usuario=self.user, nombre=nombre)
            if not self.instance.es_predefinida:
                existentes = existentes.exclude(pk=self.instance.pk)
            if existentes.exists():
                self.add_error('nombre', 'Ya tienes una plantilla con este nombre. Elige otro.')
        return datos

    class Meta:
        model = Plantilla
        fields = ['nombre', 'descripcion', 'categoria', 'ancho_tablero', 'alto_tablero', 'unidad_medida', 'piezas', 'permitir_rotacion', 'margen_corte']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Cocina Estándar, Mueble de TV'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción de la plantilla'
            }),
            'categoria': forms.Select(attrs={
                'class': 'form-select'
            }),
            'ancho_tablero': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.1'
            }),
            'alto_tablero': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.1'
            }),
            'unidad_medida': forms.Select(attrs={
                'class': 'form-select'
            }),
            'piezas': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 8,
                'placeholder': 'Formato: nombre,ancho,alto,cantidad (una por línea)\n\nEjemplos:\nPuerta,80,200,2\nCajón,40,50,4\nFondo,85,198,1\nTravesaño,70,2,4\n\nCada línea debe tener EXACTAMENTE 4 valores separados por comas.'
            }),
            'permitir_rotacion': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'margen_corte': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': '0',
                'max': '10'
            }),
        }
        labels = {
            'nombre': 'Nombre de la Plantilla',
            'descripcion': 'Descripción',
            'categoria': 'Categoría',
            'ancho_tablero': 'Ancho del tablero',
            'alto_tablero': 'Alto del tablero',
            'unidad_medida': 'Unidad de Medida',
            'piezas': 'Piezas (formato: nombre,ancho,alto,cantidad)',
            'permitir_rotacion': 'Permitir Rotación',
            'margen_corte': 'Margen de Corte (mm)',
        }
    
    def clean_piezas(self):
        piezas = self.cleaned_data.get('piezas', '').strip()
        piezas = '\n'.join(('Pieza,' + linea if len(linea.split(',')) == 3 else linea) for linea in piezas.splitlines() if linea.strip())
        if not piezas:
            raise forms.ValidationError("Debes ingresar al menos una pieza.")
        
        # Validar formato
        lineas_validas = 0
        for linea in piezas.splitlines():
            if linea.strip():
                partes = linea.split(',')
                if len(partes) != 4:
                    raise forms.ValidationError(
                        f"❌ Línea inválida: '{linea}'\n\n"
                        f"Esperado: nombre,ancho,alto,cantidad\n\n"
                        f"Ejemplo correcto:\n"
                        f"Puerta,80,200,2"
                    )
                try:
                    ancho = float(partes[1].strip())
                    alto = float(partes[2].strip())
                    cantidad = int(partes[3].strip())
                    
                    if not math.isfinite(ancho) or not math.isfinite(alto) or ancho <= 0 or alto <= 0 or cantidad <= 0:
                        raise forms.ValidationError(
                            f"❌ Valores en línea '{linea}' no pueden ser negativos o cero.\n"
                            f"Ancho: {ancho}, Alto: {alto}, Cantidad: {cantidad}"
                        )
                except ValueError as e:
                    raise forms.ValidationError(
                        f"❌ Valores numéricos inválidos en línea: '{linea}'\n\n"
                        f"Asegúrate de que:\n"
                        f"- Nombre: texto (puede incluir espacios)\n"
                        f"- Ancho: número\n"
                        f"- Alto: número\n"
                        f"- Cantidad: número entero"
                    )
                if not partes[0].strip() or len(partes[0].strip()) > 50:
                    raise forms.ValidationError('Cada pieza necesita un nombre de hasta 50 caracteres.')
                if cantidad > 100:
                    raise forms.ValidationError('La cantidad debe estar entre 1 y 100 por tipo de pieza.')
                lineas_validas += 1
        
        if lineas_validas == 0:
            raise forms.ValidationError("Debes ingresar al menos una pieza válida.")
        
        return piezas
    
    def clean_margen_corte(self):
        margen = self.cleaned_data.get('margen_corte')
        if margen is not None:
            if not math.isfinite(margen) or not 0 <= margen <= 10:
                raise forms.ValidationError('El margen debe estar entre 0 y 10 mm.')
            # Convertir de mm a cm para almacenar
            return margen / 10.0
        return 0.3  # Valor por defecto
