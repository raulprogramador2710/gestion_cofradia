from django import forms
from django.core.exceptions import ValidationError
from .models import Hermano, Estado, FormaPago, FormaComunicacion, Cofradia, Tarea, Evento, Inventario, Prestamo, Donacion

class EstadoForm(forms.ModelForm):
    class Meta:
        model = Estado
        fields = ['nombre']

class FormaPagoForm(forms.ModelForm):
    class Meta:
        model = FormaPago
        fields = ['nombre']

class FormaComunicacionForm(forms.ModelForm):
    class Meta:
        model = FormaComunicacion
        fields = ['nombre']

class CofradiaForm(forms.ModelForm):
    class Meta:
        model = Cofradia
        fields = ['nombre', 'descripcion', 'color']



class HermanoForm(forms.ModelForm):
    class Meta:
        model = Hermano
        fields = ['numero_hermano', 'dni', 'nombre', 'apellidos', 'telefono', 'direccion', 'localidad', 'fecha_nacimiento', 'fecha_inicio', 'fecha_ultimo_pago', 'email', 'iban', 'estado', 'forma_pago', 'forma_comunicacion']
         
class EventoForm(forms.ModelForm):
    class Meta:
        model = Evento
        fields = ['nombre', 'fecha', 'tipo']       
    
class TareaForm(forms.ModelForm):
    class Meta:
        model = Tarea
        fields = ['titulo', 'descripcion', 'asignado_a', 'fecha_limite', 'estado', 'prioridad']

class InventarioForm(forms.ModelForm):
    class Meta:
        model = Inventario
        fields = ['nombre', 'descripcion', 'cantidad_total', 'cantidad_disponible', 'ubicacion']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 4}),
        }

class PrestamoForm(forms.ModelForm):
    class Meta:
        model = Prestamo
        fields = ['hermano', 'inventario', 'fecha_prestamo', 'fecha_devolucion', 'estado_material', 'comentario', 'fianza', 'cofradia']
        widgets = {
            'fecha_prestamo': forms.DateInput(attrs={'type': 'date'}),
            'fecha_devolucion': forms.DateInput(attrs={'type': 'date'}),
            'comentario': forms.Textarea(attrs={'rows': 3}),
        }

class DonacionForm(forms.ModelForm):
    class Meta:
        model = Donacion
        fields = ['donante', 'cantidad', 'fecha', 'cofradia', 'evento']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['evento'].queryset = Evento.objects.all()  # Asegura que carga eventos
        self.fields['evento'].label_from_instance = lambda obj: obj.nombre  # Muestra el nombre del evento





class CargarExcelForm(forms.Form):
    archivo_excel = forms.FileField(label="Seleccionar archivo Excel", widget=forms.ClearableFileInput(attrs={'accept': '.xlsx, .xls'}))
