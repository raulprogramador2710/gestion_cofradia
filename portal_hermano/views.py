from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages

from gestion_cofradia.models import Hermano, Perfil, Tarea, Evento, Notificacion, Documento
from datetime import datetime

import logging

logger = logging.getLogger(__name__)

def login_view(request):
    if request.user.is_authenticated:
        return redirect('portal_hermano:dashboard')

    username = ''

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            # Solo comprobamos que tenga perfil
            if not Perfil.objects.filter(user=user).exists():
                messages.error(request, 'No tienes acceso al portal.')
                return render(request, 'login_portal.html', {'username': username})

            login(request, user)
            return redirect('portal_hermano:dashboard')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')

    return render(request, 'login_portal.html', {'username': username})

@login_required
def logout_view(request):
    logger.info(f"Usuario {request.user} (ID: {request.user.id}) cerrando sesión.")
    logout(request)
    return redirect('portal_hermano:login')

def get_perfil(request):
    try:
        return Perfil.objects.get(user=request.user)
    except Perfil.DoesNotExist:
        return None

def get_hermano(request):
    try:
        return Hermano.objects.get(user=request.user)
    except Hermano.DoesNotExist:
        return None

@login_required
def dashboard(request):
    perfil = get_perfil(request)
    if perfil is None:
        messages.error(request, "No tienes acceso al portal.")
        return redirect('portal_hermano:error_no_hermano')

    hermano = get_hermano(request)

    nombre = hermano.nombre if hermano else ''
    apellidos = hermano.apellidos if hermano else ''
    num_hermano = hermano.num_hermano if hermano else ''

    tareas = Tarea.objects.filter(responsable=request.user, estado__in=['pendiente', 'en_progreso'])[:5]
    total_tareas = tareas.count()

    hoy = datetime.now().date()
    eventos = Evento.objects.filter(fecha__gte=hoy).order_by('fecha')[:5]
    total_eventos = eventos.count()

    notificaciones = Notificacion.objects.filter(destinatario=request.user).order_by('-fecha_envio')[:5]
    total_notificaciones = notificaciones.count()

    cuotas_pendientes = hermano.cuotas_pendientes() if hermano else []
    total_cuotas_pendientes = cuotas_pendientes.count() if hermano else 0

    context = {
        'nombre': nombre,
        'apellidos': apellidos,
        'num_hermano': num_hermano,
        'hermano': hermano,
        'perfil': perfil,
        'tareas': tareas,
        'total_tareas': total_tareas,
        'eventos': eventos,
        'total_eventos': total_eventos,
        'notificaciones': notificaciones,
        'total_notificaciones': total_notificaciones,
        'cuotas_pendientes': cuotas_pendientes,
        'total_cuotas_pendientes': total_cuotas_pendientes,
    }
    return render(request, 'dashboard.html', context)

@login_required
def error_no_hermano(request):
    return render(request, 'error_no_hermano.html')

@login_required
def datos_personales(request):
    hermano = get_hermano(request)
    if hermano is None:
        return redirect('portal_hermano:error_no_hermano')
    return render(request, 'ver_datos_personales.html', {'hermano': hermano})

@login_required
def ver_tareas(request):
    tareas_qs = Tarea.objects.filter(
        responsable=request.user,
        estado__in=['pendiente', 'en_progreso']
    ).order_by('fecha_limite')

    paginator = Paginator(tareas_qs, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'ver_tareas.html', {'tareas': page_obj})

@login_required
def ver_eventos(request):
    hoy = datetime.now().date()
    eventos_qs = Evento.objects.filter(fecha__gte=hoy).order_by('fecha')

    paginator = Paginator(eventos_qs, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'ver_eventos.html', {'eventos': page_obj})

@login_required
def ver_notificaciones(request):
    notificaciones = Notificacion.objects.filter(destinatario=request.user).order_by('-fecha_envio')
    return render(request, 'ver_notificaciones.html', {'notificaciones': notificaciones})

@login_required
def ver_cuotas(request):
    hermano = get_hermano(request)
    if hermano is None:
        return redirect('portal_hermano:error_no_hermano')

    cuotas_pendientes = hermano.cuotas_pendientes()
    return render(request, 'ver_cuotas.html', {'cuotas_pendientes': cuotas_pendientes})

@login_required
def ver_documentos(request):
    documentos_publicos = Documento.objects.filter(visibilidad=Documento.PUBLICO)
    return render(request, 'ver_documentos.html', {'documentos': documentos_publicos})

@login_required
def cambiar_password(request):
    hermano = get_hermano(request)
    if hermano is None:
        return redirect('portal_hermano:error_no_hermano')

    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Tu contraseña ha sido cambiada correctamente.')
            return redirect('portal_hermano:dashboard')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = PasswordChangeForm(user=request.user)

    return render(request, 'password/cambiar_password.html', {'form': form})