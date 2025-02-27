# gestion_cofradia/forms.py
from django import forms
from .models import Hermano, Cofradia

class HermanoForm(forms.ModelForm):

    fecha_nacimiento = forms.DateField(input_formats=['%d/%m/%Y'])

    class Meta:
        model = Hermano
        fields = ['dni', 'nombre', 'apellidos', 'telefono', 'direccion', 'localidad', 'fecha_nacimiento', 'fecha_inicio', 'email', 'iban', 'estado', 'forma_pago', 'forma_comunicacion', 'cofradia']

    def __init__(self, *args, **kwargs):
        cofradias = kwargs.pop('cofradias', None)
        super(HermanoForm, self).__init__(*args, **kwargs)
        
        if cofradias:
            self.fields['cofradia'].queryset = cofradias  # Filtramos cofradías por el QuerySet pasado