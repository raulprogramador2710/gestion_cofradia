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
    identificador = models.IntegerField(null=True, blank=True)
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    cofradia = models.ForeignKey(Cofradia, on_delete=models.CASCADE, null=True)
    cargo = models.ForeignKey(Cargo, on_delete=models.SET_NULL, null=True, default=None)

    def __str__(self):
        return self.usuario.username

class Estado(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre

class FormaPago(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre

class FormaComunicacion(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre




class Hermano(models.Model):
    numero_hermano = models.IntegerField(null=True, blank=True)
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
        ('PAGO', 'Registro de Pago'),
        ('CAMBIO_ESTADO', 'Cambio de Estado'),
    )
    identificador = models.IntegerField(null=True, blank=True)
    hermano = models.ForeignKey('Hermano', on_delete=models.CASCADE)
    accion = models.CharField(max_length=20, choices=ACCIONES)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    fecha = models.DateTimeField(auto_now_add=True)
    detalles = models.TextField(null=True, blank=True)  # Para registrar cambios específicos
    cofradia = models.ForeignKey(Cofradia, on_delete=models.SET_NULL, null=True, default=None)

    def __str__(self):
        return f"{self.accion} - {self.hermano} - {self.fecha}"

class Evento(models.Model):
    identificador = models.IntegerField(null=True, blank=True)
    nombre = models.CharField(max_length=100)
    fecha = models.DateField()
    tipo = models.CharField(max_length=50, choices=[('Ensayo', 'Ensayo'), ('Procesión', 'Procesión'), ('Reunión', 'Reunión')])
    cofradia = models.ForeignKey(Cofradia, on_delete=models.SET_NULL, null=True, default=None)

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
    
    identificador = models.IntegerField(null=True, blank=True)
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    asignado_a = models.CharField(max_length=200)
    fecha_limite = models.DateField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='Pendiente')
    prioridad = models.CharField(max_length=10, choices=PRIORIDAD_CHOICES, default='Media')
    cofradia = models.ForeignKey(Cofradia, on_delete=models.SET_NULL, null=True, default=None)

    def __str__(self):
        return self.titulo

class Finanza(models.Model):
    identificador = models.IntegerField(null=True, blank=True)
    TIPOS = [('Ingreso', 'Ingreso'), ('Gasto', 'Gasto')]
    tipo = models.CharField(max_length=10, choices=TIPOS)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha = models.DateField(auto_now_add=True)
    cofradia = models.ForeignKey(Cofradia, on_delete=models.SET_NULL, null=True, default=None)

class Inventario(models.Model):
    identificador = models.IntegerField(null=True, blank=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    cantidad_total = models.PositiveIntegerField(null=True)
    cantidad_disponible = models.PositiveIntegerField()
    ubicacion = models.CharField(max_length=200)
    cofradia = models.ForeignKey(Cofradia, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.nombre

class Prestamo(models.Model):
    identificador = models.IntegerField(null=True, blank=True)
    hermano = models.ForeignKey(Hermano, on_delete=models.CASCADE)
    inventario = models.ForeignKey(Inventario, on_delete=models.CASCADE)
    fecha_prestamo = models.DateField()
    fecha_devolucion = models.DateField(null=True, blank=True)
    estado_material = models.CharField(max_length=100)  # Ejemplo: 'En buen estado', 'Dañado', etc.
    comentario = models.TextField()
    fianza = models.CharField(max_length=100)
    cofradia = models.ForeignKey(Cofradia, on_delete=models.SET_NULL, null=True, default=None)
    
    def __str__(self):
        return f"Préstamo de {self.inventario.nombre} a {self.hermano.nombre}"
    
class Donacion(models.Model):
    identificador = models.IntegerField(null=True, blank=True)
    donante = models.CharField(max_length=100)  # Nombre del donante (particular o empresa)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)  # Monto de la donación
    fecha = models.DateField()  # Fecha de la donación
    cofradia = models.ForeignKey(Cofradia, on_delete=models.CASCADE)  # Cofradía a la que pertenece la donación
    evento = models.ForeignKey('Evento', null=True, blank=True, on_delete=models.CASCADE)  # (Opcional) Evento asociado
    #gasto = models.ForeignKey('Gasto', null=True, blank=True, on_delete=models.CASCADE)  # (Opcional) Gasto asociado

    def __str__(self):
        return f"Donación de {self.donante} - {self.cantidad}€"

