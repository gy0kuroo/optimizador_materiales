from django import forms

class TableroForm(forms.Form):
    ancho = forms.IntegerField(label="Ancho del tablero (cm)", min_value=1)
    alto = forms.IntegerField(label="Alto del tablero (cm)", min_value=1)


class PiezaForm(forms.Form):
    ancho = forms.IntegerField(label="Ancho (cm)", min_value=1)
    alto = forms.IntegerField(label="Alto (cm)", min_value=1)
    cantidad = forms.IntegerField(label="Cantidad", min_value=1)
