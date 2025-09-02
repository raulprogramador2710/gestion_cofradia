import calendar

from django.shortcuts import render, redirect, get_object_or_404
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from django.utils import timezone

from gestion_cofradia.models import Noticia, Evento

from .forms import HazteHermanoForm

def inicio(request):
    # últimas 3 noticias
    noticias = Noticia.objects.filter(publico=True).order_by("-fecha_publicacion")[:3]

    # fecha actual
    today = timezone.localdate()
    year, month = today.year, today.month

    # eventos de este mes
    eventos = Evento.objects.filter(
        fecha__year=year, fecha__month=month, es_interno=False
    ).order_by("fecha")

    # diccionario con eventos por día
    eventos_por_dia = {}
    for ev in eventos:
        dia = ev.fecha.date()
        eventos_por_dia.setdefault(dia, []).append(ev)

    # construir calendario con eventos incluidos
    cal = calendar.Calendar(firstweekday=0)  # lunes=0
    weeks = []
    
    for week in cal.monthdatescalendar(year, month):
        week_data = []
        for day in week:
            day_data = {
                'date': day,
                'day_number': day.day,
                'is_current_month': day.month == month,
                'is_today': day == today,
                'eventos': eventos_por_dia.get(day, [])
            }
            week_data.append(day_data)
        weeks.append(week_data)

    context = {
        "titulo_pagina": "Inicio",
        "noticias": noticias,
        "weeks": weeks,
        "month": month,
        "year": year,
        "today": today,
    }
    return render(request, "inicio_web.html", context)

def hazte_hermano(request):
    if request.method == "POST":
        form = HazteHermanoForm(request.POST)
        if form.is_valid():
            nombre = form.cleaned_data["nombre"]
            email = form.cleaned_data["email"]
            telefono = form.cleaned_data["telefono"]
            direccion = form.cleaned_data["direccion"]
            comentario = form.cleaned_data["comentario"]

            # Construir mensaje
            subject = f"Solicitud de ingreso de {nombre}"
            mensaje = (
                f"Se ha recibido una nueva solicitud para hacerse hermano.\n\n"
                f"📌 Nombre: {nombre}\n"
                f"📧 Email: {email}\n"
                f"📞 Teléfono: {telefono}\n"
                f"🏠 Dirección: {direccion}\n\n"
                f"💬 Comentarios:\n{comentario}"
            )

            send_mail(
                subject,
                mensaje,
                settings.DEFAULT_FROM_EMAIL,
                [settings.EMAIL_HERMANDAD],  # Dirección a la que llegará
                fail_silently=False,
            )
            messages.success(request, "Tu solicitud ha sido enviada. La Hermandad se pondrá en contacto contigo.")
            return redirect("web_publica:hazte_hermano")
    else:
        form = HazteHermanoForm()

    return render(request, "hazte_hermano.html", {"form": form})

def noticias(request):
    # solo noticias públicas
    noticias = Noticia.objects.filter(publico=True)
    return render(request, "noticias.html", {"noticias": noticias})

def noticia_detalle(request, id):
    noticia = get_object_or_404(Noticia, id=id, publico=True)
    return render(request, "noticia_detalle.html", {"noticia": noticia})

# Historia Cofradía
def historia_cofradia(request):
    return render(request, "historia_cofradia.html")

# Historia Cristo
def titular_cristo(request):
    return render(request, "titular_cristo.html")

# Historia Virgen
def titular_virgen(request):
    return render(request, "titular_virgen.html")

