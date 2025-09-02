# web_publica/forms.py
from django import forms

class HazteHermanoForm(forms.Form):
    nombre = forms.CharField(label="Nombre completo", max_length=100, required=True)
    email = forms.EmailField(label="Correo electrónico", required=True)
    telefono = forms.CharField(label="Teléfono de contacto", max_length=15, required=True)
    direccion = forms.CharField(label="Dirección", widget=forms.Textarea(attrs={"rows": 2}), required=True)
    comentario = forms.CharField(label="Motivo / Comentarios", widget=forms.Textarea(attrs={"rows": 3}), required=False)