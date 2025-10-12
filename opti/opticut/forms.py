from django import forms

class TableroForm(forms.Form):
    ancho = forms.IntegerField(label="Ancho del tablero (cm)", min_value=1)
    alto = forms.IntegerField(label="Alto del tablero (cm)", min_value=1)
    piezas = forms.CharField(
        label="Piezas (formato: ancho,alto,cantidad por línea)",
        widget=forms.Textarea(attrs={'rows': 5}),
        help_text="Ejemplo:\n500,500,8\n1000,1500,2\n200,100,3"
    )
