from django import forms
from gestion_cofradia.models import Cofradia, Hermano

class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)
    cofradia = forms.ModelChoiceField(queryset=Cofradia.objects.none(), empty_label="Seleccione Cofradía")

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            # Mostrar solo cofradías donde el usuario es hermano
            cofradias = Cofradia.objects.filter(hermanos__user=user).distinct()
            self.fields['cofradia'].queryset = cofradias
        else:
            self.fields['cofradia'].queryset = Cofradia.objects.all()