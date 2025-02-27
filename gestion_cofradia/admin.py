# gestion_cofradia/admin.py
from django import forms
from django.contrib import admin
from .models import Estado, FormaPago, FormaComunicacion, Cofradia, Hermano, PerfilUsuario

# Crear un formulario personalizado para el modelo Hermano
class HermanoForm(forms.ModelForm):
    class Meta:
        model = Hermano
        fields = '__all__'
        widgets = {
            'fecha_nacimiento': forms.DateInput(format='%d/%m/%Y', attrs={'type': 'date'}),  # Personaliza el campo de fecha
        }

    def clean_fecha_nacimiento(self):
        return self.cleaned_data['fecha_nacimiento']

# Crear una clase de administración personalizada para Hermano
class HermanoAdmin(admin.ModelAdmin):
    form = HermanoForm  # Usar el formulario personalizado

# Crear una clase de administración personalizada para PerfilUsuario
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'es_secretario')  # Mostrar en la lista de admin
    search_fields = ('usuario__username',)  # Hacer que se pueda buscar por nombre de usuario

# Registrar los modelos con las clases personalizadas
admin.site.register(Estado)
admin.site.register(FormaPago)
admin.site.register(FormaComunicacion)
admin.site.register(Cofradia)
admin.site.register(Hermano, HermanoAdmin)  # Registrar con la clase HermanoAdmin
admin.site.register(PerfilUsuario, PerfilUsuarioAdmin)  # Registrar con la clase PerfilUsuarioAdmin
