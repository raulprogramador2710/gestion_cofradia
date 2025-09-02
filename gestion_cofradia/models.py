from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse

class Perfil(models.Model):
    ROLES = [
        ('hermano', 'Hermano'),
        ('secretario', 'Secretario'),
        ('tesorero', 'Tesorero'),
        ('hermano_mayor', 'Hermano Mayor'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rol = models.CharField(max_length=20, choices=ROLES, default='hermano')

    def __str__(self):
        return f"{self.user.username} ({self.rol})"

class FormaPago(models.Model):
    nombre = models.CharField(max_length=100, unique=True, db_index=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name_plural = "Formas de Pago"

class FormaComunicacion(models.Model):
    nombre = models.CharField(max_length=100, unique=True, db_index=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name_plural = "Formas de Comunicación"

class EstadoHermano(models.Model):
    nombre = models.CharField(max_length=50, unique=True, db_index=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Estado del Hermano"
        verbose_name_plural = "Estados de los Hermanos"

class Hermano(models.Model):
    ROLES = [
        ('costalero', 'Costalero'),
        ('mantilla', 'Mantilla'),
        ('nazareno', 'Nazareno'),
        ('insignia', 'Insignia'),
        ('hermano', 'Hermano'),
    ]

    num_hermano = models.PositiveIntegerField(unique=True, help_text="Número interno único", db_index=True)
    dni = models.CharField(max_length=10, null=True, blank=True, unique=True, db_index=True)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, help_text="Usuario asociado para portal hermano")
    nombre = models.CharField(max_length=100, db_index=True)
    apellidos = models.CharField(max_length=150, db_index=True)
    telefono = models.CharField(max_length=20, null=True, blank=True)
    direccion = models.CharField(max_length=255)
    localidad = models.CharField(max_length=100)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    fecha_inicio_cofradia = models.IntegerField(null=True, blank=True)
    fecha_ultimo_pago = models.IntegerField(null=True, blank=True)
    estado = models.ForeignKey(EstadoHermano, on_delete=models.SET_NULL, null=True, blank=True, related_name='hermanos')
    forma_pago = models.ForeignKey('FormaPago', on_delete=models.CASCADE, default=1)
    forma_comunicacion = models.ForeignKey('FormaComunicacion', on_delete=models.CASCADE, default=1)
    email = models.EmailField(null=True, blank=True)
    lopd = models.FileField(upload_to='lopd_files/', null=True, blank=True)
    rol = models.CharField(max_length=20, choices=ROLES, default='hermano')
    iban = models.CharField(max_length=34, null=True, blank=True)

    class Meta:
        verbose_name_plural = "Hermanos"

    def __str__(self):
        return f"{self.nombre} {self.apellidos} (#{self.num_hermano} - {self.dni})"

    def tiene_cuotas_pendientes(self):
        cuotas_activas = Cuota.objects.filter(activa=True)
        for cuota in cuotas_activas:
            if not self.pagos.filter(cuota=cuota).exists():
                return True
        return False

    def cuotas_pendientes(self):
        cuotas_activas = Cuota.objects.filter(activa=True)
        cuotas_pagadas = self.pagos.values_list('cuota_id', flat=True)
        return cuotas_activas.exclude(id__in=cuotas_pagadas)
    
class Cuota(models.Model):
    TIPO_CUOTA = [
        ('anual', 'Anual'),
        ('extraordinaria', 'Extraordinaria'),
    ]

    tipo = models.CharField(max_length=20, choices=TIPO_CUOTA, db_index=True)
    anio = models.PositiveIntegerField(db_index=True)
    importe = models.DecimalField(max_digits=8, decimal_places=2)
    descripcion = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_vencimiento = models.DateField(null=True, blank=True)
    activa = models.BooleanField(default=True)

    class Meta:
        unique_together = ('tipo', 'anio')
        ordering = ['-anio', 'tipo']
        verbose_name_plural = "Cuotas"

    def __str__(self):
        return f"{self.get_tipo_display()} {self.anio} - {self.importe}€ ({self.cofradia.nombre})"

class Pago(models.Model):
    METODOS_PAGO = [
        ('efectivo', 'Efectivo'),
        ('transferencia', 'Transferencia'),
        ('domiciliacion', 'Domiciliación'),
        ('tarjeta', 'Tarjeta'),
        ('bizum', 'Bizum'),
    ]

    hermano = models.ForeignKey(Hermano, on_delete=models.CASCADE, related_name='pagos')
    cuota = models.ForeignKey(Cuota, on_delete=models.CASCADE, related_name='pagos')
    fecha_pago = models.DateField(db_index=True)
    metodo = models.CharField(max_length=50, choices=METODOS_PAGO)
    importe_pagado = models.DecimalField(max_digits=8, decimal_places=2)
    observaciones = models.TextField(blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    registrado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-fecha_pago']
        verbose_name_plural = "Pagos"

    def __str__(self):
        return f"Pago {self.cuota} por {self.hermano} - {self.importe_pagado}€"

class Evento(models.Model):
    TIPO_EVENTO_CHOICES = [
        ('reunion', 'Reunión'),
        ('culto', 'Culto'),
        ('misa', 'Misa'),
        ('procesion', 'Procesión'),
    ]

    nombre = models.CharField(max_length=150, db_index=True)
    descripcion = models.TextField(blank=True, null=True)
    fecha = models.DateTimeField(db_index=True)
    lugar = models.CharField(max_length=150, blank=True, null=True)
    comentarios = models.TextField(blank=True, null=True)
    es_interno = models.BooleanField(default=False)
    notificar = models.BooleanField(default=True)
    cuota_extra = models.ForeignKey(Cuota, null=True, blank=True, on_delete=models.SET_NULL)
    tipo = models.CharField(max_length=20, choices=TIPO_EVENTO_CHOICES, default='reunion')

    def __str__(self):
        return f"{self.nombre} ({self.fecha.strftime('%d/%m/%Y %H:%M')})"

    class Meta:
        verbose_name_plural = "Eventos"

class Enser(models.Model):
    
    nombre = models.CharField(max_length=100, db_index=True)
    descripcion = models.TextField(blank=True, null=True)
    tipo = models.CharField(max_length=50, db_index=True)
    estado = models.CharField(max_length=50)
    identificador = models.CharField(max_length=50, unique=True, db_index=True,
                                    help_text="Código único para identificar el enser (ejemplo: nº inventario)")

    def __str__(self):
        return f"{self.nombre} ({self.identificador})"

    class Meta:
        verbose_name_plural = "Enseres"

class Alquiler(models.Model):
    ESTADOS_ALQUILER = [
        ('solicitado', 'Solicitado'),
        ('prestado', 'Prestado'),
        ('devuelto', 'Devuelto'),
    ]

    hermano = models.ForeignKey(Hermano, on_delete=models.CASCADE, related_name='alquileres')
    enser = models.ForeignKey(Enser, on_delete=models.CASCADE, related_name='alquileres')
    evento = models.ForeignKey(Evento, null=True, blank=True, on_delete=models.SET_NULL)
    fecha_entrega = models.DateField(db_index=True)
    fecha_devolucion = models.DateField(null=True, blank=True)
    fianza = models.DecimalField(max_digits=8, decimal_places=2)
    estado = models.CharField(max_length=20, choices=ESTADOS_ALQUILER, default='solicitado')

    def __str__(self):
        return f"Alquiler {self.estado} de {self.enser} para {self.hermano} en evento {self.evento}"

    class Meta:
        verbose_name_plural = "Alquileres"

class Notificacion(models.Model):
    TIPO_NOTIFICACION = [
        ('cuota', 'Cuota'),
        ('evento', 'Evento'),
        ('general', 'General'),
    ]

    destinatario = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE, related_name='notificaciones')
    grupo_destinatarios = models.CharField(max_length=255, null=True, blank=True, help_text="Filtro para grupo de hermanos (ej: estado=activo, rol=nazareno)")
    titulo = models.CharField(max_length=100, db_index=True)
    cuerpo = models.TextField()
    enviada = models.BooleanField(default=False)
    fecha_envio = models.DateTimeField(null=True, blank=True, db_index=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True, db_index=True)
    leida = models.BooleanField(default=False)
    tipo = models.CharField(max_length=20, choices=TIPO_NOTIFICACION, default='general', db_index=True)
    cuota = models.ForeignKey(Cuota, null=True, blank=True, on_delete=models.SET_NULL, related_name='notificaciones')

    def __str__(self):
        if self.destinatario:
            return f"Notificación individual para {self.destinatario} vía {self.destinatario.perfil.cofradia.nombre}"
        else:
            return f"Notificación grupal ({self.grupo_destinatarios}) vía {self.canal}"

    class Meta:
        verbose_name_plural = "Notificaciones"

class Tarea(models.Model):
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('en_progreso', 'En progreso'),
        ('completada', 'Completada'),
        ('cancelada', 'Cancelada'),
    ]
    titulo = models.CharField(max_length=200, db_index=True)
    descripcion = models.TextField(blank=True, null=True)
    fecha_limite = models.DateField(null=True, blank=True, db_index=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    responsable = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='tareas_asignadas')
    creada_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='tareas_creadas')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_completada = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.titulo

    class Meta:
        verbose_name_plural = "Tareas"

class Documento(models.Model):
    titulo = models.CharField(max_length=255, verbose_name="Título", db_index=True)
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    archivo = models.FileField(upload_to='documentos/', verbose_name="Archivo")
    fecha_subida = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Subida", db_index=True)
    subido_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Subido por")
    
    # Opciones de visibilidad
    PUBLICO = 'publico'
    PRIVADO = 'privado'
    VISIBILIDAD_CHOICES = [
        (PUBLICO, 'Público'),
        (PRIVADO, 'Privado'),
    ]
    visibilidad = models.CharField(
        max_length=10,
        choices=VISIBILIDAD_CHOICES,
        default=PRIVADO,
        verbose_name="Visibilidad"
    )
    
    def __str__(self):
        return self.titulo

    class Meta:
        verbose_name = "Documento"
        verbose_name_plural = "Documentos"
        ordering = ['-fecha_subida']

class Noticia(models.Model):
    titulo = models.CharField(max_length=200)
    cuerpo = models.TextField()
    imagen = models.ImageField(upload_to="noticias/", blank=True, null=True)
    fecha_publicacion = models.DateTimeField(auto_now_add=True)
    publico = models.BooleanField(default=True, help_text="Visible en web pública")

    class Meta:
        ordering = ["-fecha_publicacion"]

    def __str__(self):
        return self.titulo
    
    def get_absolute_url(self):
        return reverse("web_publica:noticia_detalle", args=[str(self.id)])


