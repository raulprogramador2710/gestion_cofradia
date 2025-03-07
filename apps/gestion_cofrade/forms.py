from django import forms
from django.core.exceptions import ValidationError
from .models import Hermano, Estado, FormaPago, FormaComunicacion, Cofradia, Tarea, Evento, Inventario, Prestamo

class HermanoForm(forms.ModelForm):
    class Meta:
        model = Hermano
        fields = ['numero_hermano', 'dni', 'nombre', 'apellidos', 'telefono', 'direccion', 'localidad', 'fecha_nacimiento', 'fecha_inicio', 'fecha_ultimo_pago', 'email', 'iban', 'estado', 'forma_pago', 'forma_comunicacion', 'cofradia']
        widgets = {
            'fecha_nacimiento': forms.DateInput(format='%d/%m/%Y', attrs={'type': 'date'}),
        }
    
    def clean_fecha_nacimiento(self):
        fecha = self.cleaned_data['fecha_nacimiento']
        try:
            # Aquí aseguramos que la fecha se esté validando en el formato correcto
            fecha_formateada = fecha.strftime('%d/%m/%Y')
        except ValueError:
            raise ValidationError("La fecha de nacimiento no tiene el formato correcto (dd/mm/yyyy).")
        return fecha
    
class EventoForm(forms.ModelForm):
    class Meta:
        model = Evento
        fields = ['nombre', 'fecha', 'tipo']
        widgets = {
            'fecha': forms.DateInput(format='%d/%m/%Y', attrs={'type': 'date'}),
        }
    
    def clean_fecha(self):
        fecha = self.cleaned_data['fecha']
        try:
            # Aquí aseguramos que la fecha se esté validando en el formato correcto
            fecha_formateada = fecha.strftime('%d/%m/%Y')
        except ValueError:
            raise ValidationError("La fecha no tiene el formato correcto (dd/mm/yyyy).")
        return fecha
    
class TareaForm(forms.ModelForm):
    class Meta:
        model = Tarea
        fields = ['titulo', 'descripcion', 'asignado_a', 'fecha_limite', 'estado', 'prioridad']
        widgets = {
            'fecha_limite': forms.DateInput(format='%d/%m/%Y', attrs={'type': 'date'}),
        }
    
    def clean_fecha_limite(self):
        fecha = self.cleaned_data['fecha_limite']
        try:
            # Aquí aseguramos que la fecha se esté validando en el formato correcto
            fecha_formateada = fecha.strftime('%d/%m/%Y')
        except ValueError:
            raise ValidationError("La fecha no tiene el formato correcto (dd/mm/yyyy).")
        return fecha

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

class CargarExcelForm(forms.Form):
    archivo_excel = forms.FileField(label="Seleccionar archivo Excel", widget=forms.ClearableFileInput(attrs={'accept': '.xlsx, .xls'}))

class InventarioForm(forms.ModelForm):
    class Meta:
        model = Inventario
        fields = ['nombre', 'descripcion', 'cantidad_disponible', 'ubicacion']

class PrestamoForm(forms.ModelForm):
    class Meta:
        model = Prestamo
        fields = ['hermano', 'inventario', 'fecha_devolucion', 'estado_material', 'comentario', 'fianza']
        widgets = {
            'fecha_prestamo': forms.HiddenInput(),
        }
