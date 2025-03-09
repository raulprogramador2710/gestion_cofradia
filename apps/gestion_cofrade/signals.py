# cofradia/signals.py
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Max
from django.db.models.signals import pre_save
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .models import Cofradia, Cargo, PerfilUsuario, Estado, FormaPago, FormaComunicacion, Hermano, AuditoriaHermano, Evento, Tarea, Finanza, Inventario, Prestamo, Donacion

# Signal para asignar el número de hermano autoincremental dentro de cada cofradía
@receiver(pre_save, sender=Hermano)
def set_numero_hermano(sender, instance, **kwargs):
    if instance.numero_hermano is None:  # Si el número no ha sido asignado aún
        # Obtener el número máximo de hermano actual en la misma cofradía
        max_numero = Hermano.objects.filter(cofradia=instance.cofradia).aggregate(Max('numero_hermano'))['numero_hermano__max']
        if max_numero is None:
            instance.numero_hermano = 1  # Si no hay hermanos, empieza con el número 1
        else:
            instance.numero_hermano = max_numero + 1  # Incrementa el número más alto para esta cofradía

# Signal para asignar el identificador autoincremental dentro de cada cofradía
@receiver(pre_save, sender=AuditoriaHermano)
@receiver(pre_save, sender=Evento)
@receiver(pre_save, sender=Tarea)
@receiver(pre_save, sender=Finanza)
@receiver(pre_save, sender=Inventario)
@receiver(pre_save, sender=Prestamo)
@receiver(pre_save, sender=Donacion)
def set_identificador(sender, instance, **kwargs):
    if instance.identificador is None:  # Si el identificador no ha sido asignado aún
        # Obtener el número máximo de identificador actual para la misma cofradía
        max_identificador = sender.objects.filter(cofradia=instance.cofradia).aggregate(Max('identificador'))['identificador__max']
        
        if max_identificador is None:
            instance.identificador = 1  # Si no hay registros previos, empieza con el número 1
        else:
            instance.identificador = max_identificador + 1  # Incrementa el número más alto para esta cofradía

# Función para crear los datos de prueba
@receiver(post_migrate)
def crear_datos_prueba(sender, **kwargs):
    # Borrar todos los datos de la Cofradía DEMO y sus dependencias
    cofradia_demo = Cofradia.objects.filter(nombre="Cofradía DEMO").first()
    if cofradia_demo:
        PerfilUsuario.objects.filter(cofradia=cofradia_demo).delete()
        User.objects.filter(username='HM_Demo').delete()

        cofradia_demo.delete()

    # Crear una nueva Cofradía DEMO
    cofradia_demo = Cofradia.objects.create(
        nombre="Cofradía DEMO",
        descripcion="Esta es una Cofradía de ejemplo para pruebas.",
        color="#ff5733"  # Color HEX de ejemplo
    )
  
    user_demo = User.objects.create_user(username='HM_Demo', password='Demo1234')
    PerfilUsuario.objects.create(usuario=user_demo, cofradia=cofradia_demo, cargo=Cargo.objects.get(cargo='Hermano Mayor'))

    
"""

"""