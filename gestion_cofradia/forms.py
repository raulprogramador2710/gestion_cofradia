from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Hermano, Cuota, Pago, Notificacion, Tarea, Documento, EstadoHermano, FormaComunicacion, Evento, Alquiler, Perfil
import csv

from django import forms
from .models import Hermano

class HermanoForm(forms.ModelForm):
    fecha_inicio_cofradia = forms.IntegerField(
        label="Año de inicio en Cofradía",
        min_value=1900,
        max_value=2100,
        widget=forms.NumberInput(attrs={'min': '1900', 'max': '2100', 'class': 'form-control'})
    )
    fecha_ultimo_pago = forms.IntegerField(
        label="Año del último pago",
        min_value=1900,
        max_value=2100,
        required=False,
        widget=forms.NumberInput(attrs={'min': '1900', 'max': '2100', 'class': 'form-control'})
    )

    class Meta:
        model = Hermano
        exclude = ['num_hermano', 'cofradia', 'user']  # Campos que se asignan automáticamente
        fields = [
            'dni', 'nombre', 'apellidos',
            'telefono', 'direccion', 'localidad', 'fecha_nacimiento',
            'fecha_inicio_cofradia', 'fecha_ultimo_pago', 'estado', 'forma_pago',
            'forma_comunicacion', 'email', 'iban', 'lopd', 'rol'
        ]
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'dni': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'apellidos': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'localidad': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'estado': forms.Select(attrs={'class': 'form-control'}),
            'rol': forms.Select(attrs={'class': 'form-control'}),
            'forma_pago': forms.Select(attrs={'class': 'form-control'}),
            'forma_comunicacion': forms.Select(attrs={'class': 'form-control'}),
            'lopd': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer que los campos fecha_nacimiento y telefono sean obligatorios
        self.fields['fecha_nacimiento'].required = True
        self.fields['telefono'].required = True
        # DNI ya no es obligatorio
        self.fields['dni'].required = False
        # El campo estado ahora mostrará todos los estados disponibles (tabla maestra)
        self.fields['estado'].queryset = EstadoHermano.objects.all()

class CuotaForm(forms.ModelForm):
    class Meta:
        model = Cuota
        fields = ['tipo', 'anio', 'importe', 'descripcion', 'fecha_vencimiento', 'activa']
        widgets = {
            'fecha_vencimiento': forms.DateInput(attrs={'type': 'date'}),
        }

class PagoForm(forms.ModelForm):
    class Meta:
        model = Pago
        fields = ['fecha_pago', 'metodo', 'importe_pagado', 'observaciones']
        widgets = {
            'fecha_pago': forms.DateInput(attrs={'type': 'date'}),
        }

class DestinatarioModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        try:
            perfil = Perfil.objects.get(user=obj)
            rol = perfil.rol
        except Perfil.DoesNotExist:
            rol = None

        roles_con_username = ['hermano_mayor', 'secretario', 'tesorero']

        if rol in roles_con_username:
            return obj.username
        else:
            try:
                hermano = Hermano.objects.get(user=obj)
                return f"{hermano.nombre} {hermano.apellidos}"
            except Hermano.DoesNotExist:
                if obj.first_name and obj.last_name:
                    return f"{obj.first_name} {obj.last_name}"
                elif obj.first_name:
                    return obj.first_name
                else:
                    return obj.username

class NotificacionForm(forms.ModelForm):
    destinatario = DestinatarioModelChoiceField(
        queryset=User.objects.none(),
        required=False,
        label="Destinatario",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Notificacion
        fields = ['destinatario', 'grupo_destinatarios', 'titulo', 'cuerpo', 'tipo']
        widgets = {
            'grupo_destinatarios': forms.TextInput(attrs={'placeholder': 'estado=activo, rol=nazareno'}),
            'cuerpo': forms.Textarea(attrs={'rows': 5}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        cofradia = kwargs.pop('cofradia', None)
        super().__init__(*args, **kwargs)
        
        if cofradia:
            usuarios = User.objects.filter(perfil__cofradia=cofradia)
            self.fields['destinatario'].queryset = usuarios

class ResponsableModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        try:
            perfil = Perfil.objects.get(user=obj)
            rol = perfil.rol
        except Perfil.DoesNotExist:
            rol = None

        roles_con_username = ['hermano_mayor', 'secretario', 'tesorero']

        if rol in roles_con_username:
            # Mostrar username (o DNI si prefieres)
            return obj.username
        else:
            # Intentar obtener nombre completo del hermano
            try:
                hermano = Hermano.objects.get(user=obj)
                return f"{hermano.nombre} {hermano.apellidos}"
            except Hermano.DoesNotExist:
                # Fallback a nombre y apellido del User
                if obj.first_name and obj.last_name:
                    return f"{obj.first_name} {obj.last_name}"
                elif obj.first_name:
                    return obj.first_name
                else:
                    return obj.username

class TareaForm(forms.ModelForm):
    responsable = ResponsableModelChoiceField(
        queryset=User.objects.all(),
        label='Responsable',
        empty_label="Seleccione un responsable",
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False
    )

    class Meta:
        model = Tarea
        fields = ['titulo', 'descripcion', 'fecha_limite', 'responsable', 'estado']
        widgets = {
            'fecha_limite': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

class DocumentoForm(forms.ModelForm):
    """
    Formulario para la creación y edición de documentos.
    """
    class Meta:
        model = Documento
        fields = ['titulo', 'descripcion', 'archivo', 'visibilidad']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
        }

class UploadHermanosForm(forms.Form):
    """
    Formulario para subir un archivo CSV con datos de hermanos.
    """
    csv_file = forms.FileField(
        label="Archivo CSV",
        help_text="Subir un archivo CSV con los datos de los hermanos."
    )

    def clean_csv_file(self):
        """
        Valida que el archivo subido sea un CSV y que tenga las columnas correctas.
        """
        csv_file = self.cleaned_data['csv_file']
        if not csv_file.name.endswith('.csv'):
            raise ValidationError("El archivo debe ser un CSV.")

        # Lee las primeras líneas para verificar las cabeceras
        try:
            reader = csv.reader(csv_file.read().decode('utf-8').splitlines())
            header = next(reader)  # Obtiene la primera línea como cabecera
            expected_headers = [
                'ID', 'DNI', 'NOMBRE', 'APELLIDOS', 'TELEFONO', 'DIRECCION',
                'LOCALIDAD', 'FECHA_NACIMIENTO', 'FECHA_INICIO', 'FECHA_ULTIMO_PAGO',
                'ESTADO', 'FORMA_PAGO', 'FORMA_COMUNICACION', 'EMAIL', 'IBAN'
            ]
            if header != expected_headers:
                raise ValidationError("Las cabeceras del CSV no coinciden con el formato esperado.")
        except Exception as e:
            raise ValidationError(f"Error al leer el archivo CSV: {e}")

        # Reinicia el puntero del archivo para que pueda ser leído de nuevo en el proceso de importación
        csv_file.seek(0)
        return csv_file

class EventoForm(forms.ModelForm):
    class Meta:
        model = Evento
        fields = ['nombre', 'descripcion', 'fecha', 'lugar', 'comentarios', 'es_interno', 'notificar', 'cuota_extra']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del evento'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Descripción del evento'
            }),
            'fecha': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'lugar': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Lugar del evento'
            }),
            'comentarios': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Comentarios adicionales'
            }),
            'es_interno': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'notificar': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'cuota_extra': forms.Select(attrs={
                'class': 'form-select'
            })
        }
        labels = {
            'nombre': 'Nombre del Evento',
            'descripcion': 'Descripción',
            'fecha': 'Fecha y Hora',
            'lugar': 'Lugar',
            'comentarios': 'Comentarios',
            'es_interno': 'Evento Interno',
            'notificar': 'Notificar a Hermanos',
            'cuota_extra': 'Cuota Extra Asociada'
        }

    def __init__(self, *args, **kwargs):
        cofradia = kwargs.pop('cofradia', None)
        super().__init__(*args, **kwargs)
        
        # Filtrar cuotas por cofradía si se proporciona
        if cofradia:
            self.fields['cuota_extra'].queryset = Cuota.objects.filter(cofradia=cofradia)
        else:
            self.fields['cuota_extra'].queryset = Cuota.objects.none()
        
        # Hacer que cuota_extra tenga opción vacía
        self.fields['cuota_extra'].empty_label = "Sin cuota extra"
        
        # Campos requeridos
        self.fields['nombre'].required = True
        self.fields['fecha'].required = True

class AlquilerForm(forms.ModelForm):
    class Meta:
        model = Alquiler
        fields = ['hermano', 'enser', 'evento', 'fecha_entrega', 'fecha_devolucion', 'fianza', 'estado']
        widgets = {
            'fecha_entrega': forms.DateInput(attrs={'type': 'date'}),
            'fecha_devolucion': forms.DateInput(attrs={'type': 'date'}),
        }


