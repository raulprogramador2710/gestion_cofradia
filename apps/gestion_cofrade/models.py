from django.db import models
from django.contrib.auth.models import User
import datetime

class Cofradia(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField()
    color = models.CharField(max_length=7, help_text="Código HEX del color (ej: #ff5733)", null=True)

    def __str__(self):
        return self.nombre
    
class Cargo(models.Model):
    cargo = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.cargo

class PerfilUsuario(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    cofradia = models.ForeignKey(Cofradia, on_delete=models.CASCADE, null=True)
    cargo = models.ForeignKey(Cargo, on_delete=models.SET_NULL, null=True, default=None)

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
    dni = models.CharField(max_length=9, null=True)
    nombre = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    telefono = models.CharField(max_length=9, null=True)
    direccion = models.CharField(max_length=255, null=True)
    localidad = models.CharField(max_length=100)
    fecha_nacimiento = models.DateField(null=True)
    fecha_inicio = models.PositiveIntegerField(default=datetime.date.today().year, null=True)
    fecha_ultimo_pago = models.PositiveIntegerField(default=datetime.date.today().year, null=True)
    email = models.EmailField(null=True)
    iban = models.CharField(max_length=24, null=True)  # IBAN puede tener hasta 34 caracteres, pero en España son 24
    estado = models.ForeignKey(Estado, on_delete=models.SET_NULL, null=True, default=None)
    forma_pago = models.ForeignKey(FormaPago, on_delete=models.SET_NULL, null=True, default=None)
    forma_comunicacion = models.ForeignKey(FormaComunicacion, on_delete=models.SET_NULL, null=True, default=None)
    cofradia = models.ForeignKey(Cofradia, on_delete=models.SET_NULL, null=True, default=None)
    cuota_pendiente = models.DecimalField(max_digits=10, decimal_places=2, default=0)

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

    def __str__(self):
        return f"{self.accion} - {self.hermano} - {self.fecha}"

class Tarea(models.Model):
    PRIORIDAD_CHOICES = [
        ('Baja', 'Baja'),
        ('Media', 'Media'),
        ('Alta', 'Alta'),
    ]
    
    ESTADO_CHOICES = [
        ('Pendiente', 'Pendiente'),
        ('En Proceso', 'En Proceso'),
        ('Completada', 'Completada'),
        ('Atrasada', 'Atrasada'),
    ]
    
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    asignado_a = models.CharField(max_length=200)
    fecha_limite = models.DateField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='Pendiente')
    prioridad = models.CharField(max_length=10, choices=PRIORIDAD_CHOICES, default='Media')
    cofradia = models.ForeignKey(Cofradia, on_delete=models.SET_NULL, null=True, default=None)

    def __str__(self):
        return self.titulo

class Evento(models.Model):
    nombre = models.CharField(max_length=100)
    fecha = models.DateField()
    tipo = models.CharField(max_length=50, choices=[('Ensayo', 'Ensayo'), ('Procesión', 'Procesión'), ('Reunión', 'Reunión')])
    cofradia = models.ForeignKey(Cofradia, on_delete=models.SET_NULL, null=True, default=None)

class Finanza(models.Model):
    TIPOS = [('Ingreso', 'Ingreso'), ('Gasto', 'Gasto')]
    tipo = models.CharField(max_length=10, choices=TIPOS)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha = models.DateField(auto_now_add=True)
    cofradia = models.ForeignKey(Cofradia, on_delete=models.SET_NULL, null=True, default=None)