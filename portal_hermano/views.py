from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from gestion_cofradia.models import Cofradia, Hermano, Perfil, Tarea, Evento, Notificacion
from datetime import datetime, timedelta

import logging

logger = logging.getLogger(__name__)

def login_view(request):
    if request.user.is_authenticated:
        return redirect('portal_hermano:dashboard')

    cofradias = Cofradia.objects.all()
    username = ''

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        cofradia_id = request.POST.get('cofradia')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            try:
                cofradia = Cofradia.objects.get(pk=cofradia_id)
            except Cofradia.DoesNotExist:
                messages.error(request, 'Cofradía seleccionada no válida.')
                return render(request, 'login_portal.html', {'cofradias': cofradias, 'username': username})

            # Verificar que el usuario tiene perfil en esa cofradía
            if not Perfil.objects.filter(user=user, cofradia=cofradia).exists():
                messages.error(request, 'No tienes acceso a la cofradía seleccionada.')
                return render(request, 'login_portal.html', {'cofradias': cofradias, 'username': username})

            login(request, user)
            request.session['cofradia_id'] = cofradia.id
            return redirect('portal_hermano:dashboard')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')

    return render(request, 'login_portal.html', {'cofradias': cofradias, 'username': username})

@login_required
def logout_view(request):
    logger.info(f"Usuario {request.user} (ID: {request.user.id}) cerrando sesión.")
    logout(request)
    request.session.pop('cofradia_id', None)
    return redirect('portal_hermano:login')

def get_perfil_y_cofradia(request):
    cofradia_id = request.session.get('cofradia_id')
    if not cofradia_id:
        return None, None
    cofradia = get_object_or_404(Cofradia, pk=cofradia_id)
    try:
        perfil = Perfil.objects.get(user=request.user, cofradia=cofradia)
    except Perfil.DoesNotExist:
        return None, cofradia
    return perfil, cofradia

def get_hermano_por_perfil(perfil):
    if not perfil:
        return None
    try:
        hermano = Hermano.objects.get(user=perfil.user, cofradia=perfil.cofradia)
    except Hermano.DoesNotExist:
        return None
    return hermano

@login_required
def dashboard(request):
    perfil, cofradia = get_perfil_y_cofradia(request)
    if perfil is None:
        messages.error(request, "No tienes acceso a la cofradía seleccionada o no estás vinculado a ningún perfil.")
        return redirect('portal_hermano:error_no_hermano')

    hermano = get_hermano_por_perfil(perfil)

    # Datos del hermano (si existe)
    nombre = hermano.nombre if hermano else ''
    apellidos = hermano.apellidos if hermano else ''
    num_hermano = hermano.num_hermano if hermano else ''

    # Tareas asignadas al usuario
    tareas = Tarea.objects.filter(responsable=request.user, estado__in=['pendiente', 'en_progreso'])[:5]
    total_tareas = tareas.count()

    # Eventos próximos 30 días
    hoy = datetime.now().date()
    eventos = Evento.objects.filter(
        cofradia=cofradia,
        fecha__gte=hoy,
        fecha__lte=hoy + timedelta(days=30)
    ).order_by('fecha')[:5]
    total_eventos = eventos.count()

    # Notificaciones recientes
    notificaciones = Notificacion.objects.filter(destinatario=request.user).order_by('-fecha_envio')[:5]
    total_notificaciones = notificaciones.count()

    # Cuotas pendientes
    cuotas_pendientes = hermano.cuotas_pendientes() if hermano else []
    total_cuotas_pendientes = cuotas_pendientes.count() if hermano else 0

    context = {
        'nombre': nombre,
        'apellidos': apellidos,
        'num_hermano': num_hermano,
        'cofradia': cofradia,
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
    perfil, _ = get_perfil_y_cofradia(request)
    hermano = get_hermano_por_perfil(perfil)
    if hermano is None:
        return redirect('portal_hermano:error_no_hermano')
    return render(request, 'ver_datos_personales.html', {'hermano': hermano})

@login_required
def ver_tareas(request):
    perfil, _ = get_perfil_y_cofradia(request)
    if perfil is None:
        messages.error(request, "No tienes acceso a la cofradía seleccionada.")
        return redirect('portal_hermano:error_no_hermano')

    # Obtener tareas asignadas al usuario logueado y que estén pendientes o en progreso
    tareas_qs = Tarea.objects.filter(
        responsable=request.user,
        estado__in=['pendiente', 'en_progreso']
    ).order_by('fecha_limite')

    # Paginación: 10 tareas por página
    paginator = Paginator(tareas_qs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'tareas': page_obj,
    }
    return render(request, 'ver_tareas.html', context)

@login_required
def ver_eventos(request):
    perfil, cofradia = get_perfil_y_cofradia(request)
    if perfil is None or cofradia is None:
        messages.error(request, "No tienes acceso a la cofradía seleccionada.")
        return redirect('portal_hermano:error_no_hermano')

    hoy = datetime.now().date()
    eventos_qs = Evento.objects.filter(
        cofradia=cofradia,
        fecha__gte=hoy,
        fecha__lte=hoy + timedelta(days=30)
    ).order_by('fecha')

    paginator = Paginator(eventos_qs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'eventos': page_obj,
    }
    return render(request, 'ver_eventos.html', context)

@login_required
def notificaciones(request):
    perfil, _ = get_perfil_y_cofradia(request)
    hermano = get_hermano_por_perfil(perfil)
    if hermano is None:
        return redirect('portal_hermano:error_no_hermano')
    # Lógica para mostrar notificaciones
    return render(request, 'notificaciones.html')

@login_required
def cuotas(request):
    perfil, _ = get_perfil_y_cofradia(request)
    hermano = get_hermano_por_perfil(perfil)
    if hermano is None:
        return redirect('portal_hermano:error_no_hermano')
    # Lógica para mostrar cuotas
    return render(request, 'cuotas.html')

@login_required
def documentos(request):
    perfil, _ = get_perfil_y_cofradia(request)
    hermano = get_hermano_por_perfil(perfil)
    if hermano is None:
        return redirect('portal_hermano:error_no_hermano')
    # Lógica para mostrar documentos
    return render(request, 'documentos.html')

@login_required
def cambiar_password(request):
    perfil, _ = get_perfil_y_cofradia(request)
    hermano = get_hermano_por_perfil(perfil)
    if hermano is None:
        return redirect('portal_hermano:error_no_hermano')
    # Lógica para cambiar contraseña
    return render(request, 'cambiar_password.html')