from django.contrib.auth.models import User
from django.db import models
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import render, redirect
from .models import Hermano
from functools import wraps


# --- CONTROL DE ROLES ---

class RoleRequiredMixin(UserPassesTestMixin):
    ROLES_LEGIBLES = ['Hermano', 'Secretario', 'Tesorero', 'Hermano Mayor']

    def test_func(self):
        try:
            perfil = self.request.user.perfil_set.first()
            rol_usuario = perfil.rol if perfil else None
            return self.request.user.is_superuser or (rol_usuario in self.roles_permitidos)
        except AttributeError:
            return False


def role_required(roles_permitidos):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            perfil = request.user.perfil_set.first()
            if not perfil:
                # No tiene perfil, redirigir a login o página de error
                return redirect('gestion_cofradia:login')
            if perfil.rol not in roles_permitidos:
                # Rol no permitido, redirigir o mostrar error
                return redirect('gestion_cofradia:acceso_denegado')  # O la url que uses
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator






def crear_hermano_con_usuario(nombre, apellidos, dni, rol, email=None):
    user = User.objects.create_user(username=dni, password='cambiar1234', email=email)
    hermano = Hermano.objects.create(
        user=user,
        nombre=nombre,
        apellidos=apellidos,
        dni=dni,
        rol=rol,
        numero_hermano=obtener_numero_hermano(),
        email=email,  # Solo si tu modelo Hermano tiene este campo
    )
    return hermano

def obtener_numero_hermano():
    max_num = Hermano.objects.all().aggregate(models.Max('numero_hermano'))['numero_hermano__max']
    return (max_num or 0) + 1


def enviar_notificaciones(notificacion):
    if notificacion.destinatario:
        # Notificación individual: usar la forma de comunicación del hermano
        enviar_por_canal(notificacion.destinatario, notificacion, notificacion.destinatario.forma_comunicacion)
    else:
        # Notificación grupal: usar la forma de comunicación elegida
        enviar_por_canal(None, notificacion, notificacion.forma_comunicacion)

def enviar_por_canal(hermano, notificacion, forma_comunicacion):
    if forma_comunicacion.nombre.lower() == 'email':
        enviar_por_email(hermano, notificacion)
    elif forma_comunicacion.nombre.lower() == 'whatsapp':
        enviar_por_whatsapp(hermano, notificacion)
    # ... otros canales

def enviar_por_email(hermano, notificacion):
    email = getattr(hermano, 'email', None) or getattr(hermano.user, 'email', None)
    if email:
        send_mail(
            subject=notificacion.titulo,
            message=notificacion.cuerpo,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )

def enviar_por_whatsapp(hermano, notificacion):
    # Implementar lógica de WhatsApp
    pass