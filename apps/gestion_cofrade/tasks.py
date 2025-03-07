# core/tasks.py
from celery import shared_task
from django.utils import timezone
from .models import Notificacion
from django.core.mail import send_mail
from .utils import enviar_whatsapp  # Asumiendo que la función está en utils.py

@shared_task
def recordatorio_evento():
    # Filtra los eventos que se deben recordar hoy
    eventos_proximos = Notificacion.objects.filter(tipo='evento', fecha_evento=timezone.now().date())
    
    for evento in eventos_proximos:
        mensaje = f"Recordatorio: {evento.mensaje}. Fecha del evento: {evento.fecha_evento}"
        
        # Enviar notificación por correo electrónico (puedes agregar la función que prefieras)
        send_mail(
            subject="Recordatorio de evento",
            message=mensaje,
            from_email="no-reply@tusitio.com",
            recipient_list=[evento.usuario.email],
        )
        
        # Enviar WhatsApp si lo necesitas
        enviar_whatsapp(evento.usuario, mensaje)
