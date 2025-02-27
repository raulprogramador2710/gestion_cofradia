from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_save, pre_delete
from django.dispatch import receiver
from django.utils import timezone

from .models import PerfilUsuario, Hermano, AuditoriaHermano

@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    if created:
        PerfilUsuario.objects.create(usuario=instance)

@receiver(post_save, sender=User)
def guardar_perfil_usuario(sender, instance, **kwargs):
    instance.perfilusuario.save()

#AUDITORIA
@receiver(pre_save, sender=Hermano)
def registrar_modificacion(sender, instance, **kwargs):
    if instance.pk:
        accion = 'MODIFICAR'
    else:
        accion = 'CREAR'
    AuditoriaHermano.objects.create(
        hermano=instance,
        accion=accion,
        usuario=instance.modified_by,
        fecha=timezone.now()
    )

@receiver(pre_delete, sender=Hermano)
def registrar_eliminacion(sender, instance, **kwargs):
    AuditoriaHermano.objects.create(
        hermano=instance,
        accion='ELIMINAR',
        usuario=instance.modified_by,
        fecha=timezone.now()
    )
