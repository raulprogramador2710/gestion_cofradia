from django.db import models
from django.contrib.auth.models import User
import datetime

class Cofradia(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField()
    color = models.CharField(max_length=7, help_text="Código HEX del color (ej: #ff5733)", null=True)

    def __str__(self):
        return self.nombre
    
class PerfilUsuario(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    cofradia = models.ForeignKey(Cofradia, on_delete=models.CASCADE, null=True)
    es_secretario = models.BooleanField(default=False)  # Define si es secretario

    def __str__(self):
        return self.usuario.username

class Estado(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre

class FormaPago(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre

class FormaComunicacion(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre

class Hermano(models.Model):
    dni = models.CharField(max_length=9, unique=True)
    nombre = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    telefono = models.CharField(max_length=9)
    direccion = models.CharField(max_length=255)
    localidad = models.CharField(max_length=100)
    fecha_nacimiento = models.DateField()
    fecha_inicio = models.PositiveIntegerField(default=datetime.date.today().year)
    fecha_ultimo_pago = models.PositiveIntegerField(default=datetime.date.today().year)
    email = models.EmailField(null=True)
    iban = models.CharField(max_length=24, null=True)  # IBAN puede tener hasta 34 caracteres, pero en España son 24
    estado = models.ForeignKey(Estado, on_delete=models.SET_NULL, null=True, default=Estado.objects.first)
    forma_pago = models.ForeignKey(FormaPago, on_delete=models.SET_NULL, null=True, default=FormaPago.objects.first)
    forma_comunicacion = models.ForeignKey(FormaComunicacion, on_delete=models.SET_NULL, null=True, default=FormaComunicacion.objects.first)
    cofradia = models.ForeignKey(Cofradia, on_delete=models.SET_NULL, null=True, default=Cofradia.objects.first)
    perfil_usuario = models.ForeignKey(PerfilUsuario, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        permissions = [
            ("puede_ver_hermanos", "Puede ver la lista de hermanos"),
            ("puede_crear_hermanos", "Puede crear hermanos"),
            ("puede_editar_hermanos", "Puede editar hermanos"),
            ("puede_eliminar_hermanos", "Puede eliminar hermanos"),
        ]

    def __str__(self):
        return f"{self.nombre} {self.apellidos}"


class AuditoriaHermano(models.Model):
    ACCIONES = (
        ('CREAR', 'Crear'),
        ('MODIFICAR', 'Modificar'),
        ('ELIMINAR', 'Eliminar'),
    )
    hermano = models.ForeignKey('Hermano', on_delete=models.CASCADE)
    accion = models.CharField(max_length=10, choices=ACCIONES)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    fecha = models.DateTimeField(auto_now_add=True)