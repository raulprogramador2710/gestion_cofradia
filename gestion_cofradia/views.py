# Python standard library
import csv
import json
import logging
from collections import Counter
from datetime import date, timedelta
from io import BytesIO
from math import ceil

# Django core
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.http import HttpResponse, JsonResponse, FileResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone
from django.utils.timezone import now
from django.views import View

# Third-party (reportlab)
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfgen import canvas

# Local imports
from .utils import RoleRequiredMixin, role_required
from .forms import (
    HermanoForm, CuotaForm, PagoForm, EventoForm, NotificacionForm,
    TareaForm, DocumentoForm, UploadHermanosForm, AlquilerForm, EnserForm
)
from .models import (
    Hermano, Cuota, Pago, Evento, Notificacion, Tarea, FormaPago,
    FormaComunicacion, Documento, EstadoHermano, Alquiler, Cofradia, Enser
)

logger = logging.getLogger(__name__)

@login_required
def logout_view(request):
    logger.info(f"Usuario {request.user} (ID: {request.user.id}) intentando cerrar sesión.")
    logout(request)
    logger.info(f"Usuario {request.user} ha cerrado sesión y será redirigido.")
    return redirect('gestion_cofradia:login')

def login_view(request):
    if request.user.is_authenticated:
        return redirect('gestion_cofradia:inicio')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('gestion_cofradia:inicio')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')
    return render(request, 'login.html')


@login_required
@role_required(roles_permitidos=['secretario', 'tesorero', 'hermano_mayor'])
def inicio(request):
    perfil = request.user.perfil_set.first()
    if not perfil:
        return redirect('gestion_cofradia:login')

    cofradia = perfil.cofradia
    rol = perfil.rol
    user = request.user

    # Tareas próximas a vencer (solo las asignadas al usuario actual o sin asignar, ordenadas por fecha más próxima)
    tareas_proximas = Tarea.objects.filter(
        Q(responsable=request.user) | Q(responsable__isnull=True),
        estado__in=['pendiente', 'en_progreso']
    ).order_by('fecha_limite')[:5]

    # Notificaciones (si tienes el modelo Notificacion relacionado con User)
    notificaciones = list(getattr(user, 'notificaciones', []).all().order_by('-fecha_envio')[:5]) if hasattr(user, 'notificaciones') else []
    total_notificaciones = len(notificaciones)

    # Solo hermanos activos o no pagados (excluye fallecidos y bajas, insensible a mayúsculas)
    hermanos = Hermano.objects.filter(
        cofradia=cofradia
    ).filter(
        Q(estado__nombre__iexact='activo') | Q(estado__nombre__iexact='no pagado')
    ).distinct()
    total_hermanos = hermanos.count()

    # Enseres pendientes de devolución (alquileres en estado "prestado")
    enseres_pendientes = Alquiler.objects.filter(
        cofradia=cofradia,
        estado='prestado'
    ).select_related('enser', 'hermano').order_by('fecha_entrega')[:5]

    context = {
        'total_hermanos': total_hermanos,
        'tareas_proximas': tareas_proximas,
        'total_notificaciones': total_notificaciones,
        'enseres_pendientes': enseres_pendientes,
        'perfil': perfil,
        # Pasamos la lista para el for en la plantilla
        'graficas': ['Estado', 'Comunicacion', 'Pago'],
    }

    if rol in ['hermano_mayor', 'secretario']:
        # Gráfica 1: Hermanos por estado (todos los hermanos de la cofradía)
        hermanos_todos = Hermano.objects.filter(cofradia=cofradia)
        hermanos_estado = []
        for h in hermanos_todos:
            if h.estado and h.estado.nombre:
                hermanos_estado.append(h.estado.nombre)
            else:
                hermanos_estado.append('Sin definir')
        hermanos_estado_count = [{'estado': k, 'total': v} for k, v in Counter(hermanos_estado).items()]

        # Gráfica 2: Hermanos por forma de comunicación (solo activos/no pagados)
        hermanos_comunicacion = []
        for h in hermanos:
            if h.forma_comunicacion:
                hermanos_comunicacion.append(h.forma_comunicacion.nombre)
            else:
                hermanos_comunicacion.append('Sin definir')
        hermanos_comunicacion_count = [{'forma_comunicacion': k, 'total': v} for k, v in Counter(hermanos_comunicacion).items()]

        # Gráfica 3: Hermanos por forma de pago (solo activos/no pagados)
        hermanos_pago = []
        for h in hermanos:
            if h.forma_pago:
                hermanos_pago.append(h.forma_pago.nombre)
            else:
                hermanos_pago.append('Sin definir')
        hermanos_pago_count = [{'forma_pago': k, 'total': v} for k, v in Counter(hermanos_pago).items()]

        # Próximos eventos (próximos 30 días)
        ahora = timezone.now()
        en_30_dias = ahora + timedelta(days=30)
        proximos_eventos = Evento.objects.filter(
            cofradia=cofradia,
            fecha__gte=ahora,
            fecha__lte=en_30_dias
        ).order_by('fecha')[:5]

        # Eventos pendientes (todos los eventos futuros)
        eventos_pendientes = Evento.objects.filter(
            cofradia=cofradia,
            fecha__gte=ahora
        ).order_by('fecha')[:5]

        context.update({
            'hermanos_estado_json': json.dumps(hermanos_estado_count),
            'hermanos_comunicacion_json': json.dumps(hermanos_comunicacion_count),
            'hermanos_pago_json': json.dumps(hermanos_pago_count),
            'proximos_eventos': proximos_eventos,
            'eventos_pendientes': eventos_pendientes,
        })

    if rol in ['hermano_mayor', 'tesorero']:
        # TESORERO y HERMANO MAYOR: Cuentas, cuotas, pagos

        cuota_activa = Cuota.objects.filter(cofradia=cofradia, activa=True).first()
        if cuota_activa:
            total_a_recaudar = cuota_activa.importe * total_hermanos
            total_recaudado = Pago.objects.filter(
                cuota=cuota_activa,
                cofradia=cofradia,
                hermano__in=hermanos
            ).aggregate(total=Sum('importe_pagado'))['total'] or 0

            hermanos_pagados_ids = Pago.objects.filter(
                cuota=cuota_activa,
                cofradia=cofradia,
                hermano__in=hermanos
            ).values_list('hermano_id', flat=True).distinct()

            total_pagados = len(hermanos_pagados_ids)
            total_no_pagados = total_hermanos - total_pagados
        else:
            total_a_recaudar = 0
            total_recaudado = 0
            total_pagados = 0
            total_no_pagados = total_hermanos

        pagos_pendientes = total_no_pagados

        context.update({
            'total_a_recaudar': total_a_recaudar,
            'total_recaudado': total_recaudado,
            'total_pagados': total_pagados,
            'total_no_pagados': total_no_pagados,
            'pagos_pendientes': pagos_pendientes,
        })

    return render(request, 'inicio.html', context)


#HERMANOS
@login_required
@role_required(roles_permitidos=['secretario', 'tesorero', 'hermano_mayor'])
def lista_hermanos(request):
    perfil = request.user.perfil_set.first()
    if not perfil:
        return redirect('gestion_cofradia:login')
    cofradia_usuario = perfil.cofradia

    # Importación CSV (si la usas)
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        try:
            decoded_file = csv_file.read().decode('utf-8')
            reader = csv.DictReader(decoded_file.splitlines())
            count = 0
            for row in reader:
                try:
                    hermano, created = Hermano.objects.get_or_create(
                        cofradia=cofradia_usuario,
                        dni=row['dni'],
                        defaults={
                            'numero': int(row['numero']),
                            'nombre': row['nombre'],
                            'apellidos': row['apellidos'],
                            'fecha_nacimiento': row['fecha_nacimiento'],
                            'direccion': row['direccion'],
                            'telefono': row['telefono'],
                            'email': row['email'],
                            'estado': row['estado'],
                            'año_ultimo_pago': int(row['año_ultimo_pago']) if row['año_ultimo_pago'] else None,
                            'forma_pago': FormaPago.objects.get(nombre=row['forma_pago']) if row['forma_pago'] else None,
                            'forma_comunicacion': FormaComunicacion.objects.get(nombre=row['forma_comunicacion']) if row['forma_comunicacion'] else None,
                        }
                    )
                    if created:
                        count += 1
                except Exception as e:
                    messages.warning(request, f"Error en la fila con DNI {row.get('dni', 'desconocido')}: {e}")
            messages.success(request, f"{count} hermanos cargados correctamente.")
            return redirect('gestion_cofradia:lista_hermanos')
        except Exception as e:
            messages.error(request, f"Error al procesar el archivo: {e}")

    # Solo renderiza el template con la tabla vacía
    # DataTables pedirá los datos a la vista hermanos_json
    return render(request, 'hermanos/lista_hermanos.html')

def hermanos_json(request):
    columns = [
        'num_hermano',
        'dni',
        'nombre',
        'apellidos',
        'telefono',
        'estado__nombre',
        'forma_pago__nombre',
        'forma_comunicacion__nombre',
    ]

    # Paginación
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    page = (start // length) + 1
    search_value = request.GET.get('search[value]', '')

    # Ordenación
    order_column = int(request.GET.get('order[0][column]', 0))
    order_dir = request.GET.get('order[0][dir]', 'asc')
    order_field = columns[order_column]
    if order_dir == 'desc':
        order_field = '-' + order_field

    # Filtro por cofradía del usuario
    perfil = request.user.perfil_set.first()
    hermanos = Hermano.objects.filter(cofradia=perfil.cofradia)

    # Búsqueda global
    if search_value:
        hermanos = hermanos.filter(
            Q(num_hermano__icontains=search_value) |
            Q(dni__icontains=search_value) |
            Q(nombre__icontains=search_value) |
            Q(apellidos__icontains=search_value) |
            Q(telefono__icontains=search_value) |
            Q(estado__nombre__icontains=search_value) |
            Q(forma_pago__nombre__icontains=search_value) |
            Q(forma_comunicacion__nombre__icontains=search_value)
        )

    total = hermanos.count()
    hermanos = hermanos.order_by(order_field)[start:start+length]

    # Calcular la página actual para los enlaces
    page = (start // length) + 1

    data = []
    for h in hermanos:
        data.append([
            h.num_hermano,
            h.dni,
            h.nombre,
            h.apellidos,
            h.telefono,
            get_estado_badge(h.estado),
            get_pago_badge(h.forma_pago),
            get_comunicacion_badge(h.forma_comunicacion),
            f'''
            <a href="/gestioncofradia/hermanos/{h.id}/?page={page}" class="btn btn-sm btn-outline-info me-1" data-bs-toggle="tooltip" title="Ver">
                <i class="fa-solid fa-eye"></i>
            </a>
            <a href="/gestioncofradia/hermanos/{h.id}/editar/?page={page}" class="btn btn-sm btn-outline-success me-1" data-bs-toggle="tooltip" title="Editar">
                <i class="fa-solid fa-pen-to-square"></i>
            </a>
            <a href="/gestioncofradia/hermanos/{h.id}/notificar/?page={page}" class="btn btn-sm btn-outline-warning" data-bs-toggle="tooltip" title="Notificar">
                <i class="fa-solid fa-bell"></i>
            </a>
            '''
        ])

    return JsonResponse({
        'draw': int(request.GET.get('draw', 1)),
        'recordsTotal': total,
        'recordsFiltered': total,
        'data': data,
    })

def get_estado_badge(estado):
    if not estado:
        return '<span class="badge bg-light text-dark">Sin estado</span>'
    nombre = estado.nombre.lower()
    if nombre == 'activo':
        return f'<span class="badge bg-success">{estado.nombre}</span>'
    elif nombre == 'no pagado':
        return f'<span class="badge bg-warning text-dark">{estado.nombre}</span>'
    elif nombre == 'baja':
        return f'<span class="badge bg-secondary">{estado.nombre}</span>'
    elif nombre == 'fallecido':
        return f'<span class="badge bg-dark">{estado.nombre}</span>'
    else:
        return f'<span class="badge bg-light text-dark">{estado.nombre}</span>'

def get_pago_badge(forma_pago):
    if forma_pago:
        return f'<span class="badge bg-info text-dark">{forma_pago.nombre}</span>'
    return '<span class="badge bg-light text-dark">Sin definir</span>'

def get_comunicacion_badge(forma_comunicacion):
    if forma_comunicacion:
        return f'<span class="badge bg-secondary">{forma_comunicacion.nombre}</span>'
    return '<span class="badge bg-light text-dark">Sin definir</span>'

@login_required
@role_required(roles_permitidos=['secretario', 'tesorero', 'hermano_mayor'])
def ver_hermano(request, pk):
    perfil = request.user.perfil_set.first()
    if not perfil:
        return redirect('gestion_cofradia:login')
    cofradia_usuario = perfil.cofradia
    hermano = get_object_or_404(Hermano, pk=pk, cofradia=cofradia_usuario)
    
    # Obtener cuotas activas que no han sido pagadas por este hermano
    cuotas_pendientes = Cuota.objects.filter(
        cofradia=cofradia_usuario, 
        activa=True
    ).exclude(
        pagos__hermano=hermano
    )
    
    # Obtener pagos realizados por este hermano
    pagos_realizados = Pago.objects.filter(hermano=hermano).order_by('-fecha_pago')
    
    context = {
        'hermano': hermano,
        'cuotas_pendientes': cuotas_pendientes,
        'pagos_realizados': pagos_realizados,
    }
    return render(request, 'hermanos/ver_hermano.html', context)

@login_required
@role_required(roles_permitidos=['secretario', 'tesorero', 'hermano_mayor'])
def crear_hermano(request):
    perfil = request.user.perfil_set.first()
    if not perfil:
        return redirect('gestion_cofradia:login')
    if request.method == 'POST':
        form = HermanoForm(request.POST, request.FILES)
        if form.is_valid():
            hermano = form.save(commit=False)
            
            # Asignar cofradía del usuario logueado
            hermano.cofradia = perfil.cofradia
            
            # Calcular num_hermano automáticamente
            ultimo_hermano = Hermano.objects.filter(cofradia=hermano.cofradia).order_by('-num_hermano').first()
            hermano.num_hermano = (ultimo_hermano.num_hermano + 1) if ultimo_hermano else 1
            
            # Crear o asociar usuario para el hermano SOLO si tiene DNI
            if hermano.dni:
                username = hermano.dni
                usuario, created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'first_name': hermano.nombre,
                        'last_name': hermano.apellidos,
                        'email': hermano.email or '',
                    }
                )
                if created:
                    usuario.set_password(username)  # Contraseña inicial = DNI
                    usuario.save()
                
                # Crear perfil solo si no existe para ese usuario y cofradía
                from .models import Perfil
                perfil_usuario, perfil_created = Perfil.objects.get_or_create(
                    user=usuario,
                    cofradia=hermano.cofradia,
                    defaults={'rol': 'hermano'}
                )
                
                hermano.user = usuario
            
            hermano.save()
            messages.success(request, f'Hermano creado correctamente. Número asignado: {hermano.num_hermano}')
            return redirect('gestion_cofradia:ver_hermano', pk=hermano.pk)
    else:
        form = HermanoForm()
    
    return render(request, 'hermanos/crear_hermano.html', {'form': form})

@login_required
@role_required(roles_permitidos=['secretario', 'tesorero', 'hermano_mayor'])
def editar_hermano(request, pk):
    perfil = request.user.perfil_set.first()
    if not perfil:
        return redirect('gestion_cofradia:login')
    hermano = get_object_or_404(Hermano, pk=pk, cofradia=perfil.cofradia)
    
    if request.method == 'POST':
        form = HermanoForm(request.POST, request.FILES, instance=hermano)
        if form.is_valid():
            hermano_actualizado = form.save(commit=False)
            
            if hermano_actualizado.dni:
                username = hermano_actualizado.dni
                usuario, created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'first_name': hermano_actualizado.nombre,
                        'last_name': hermano_actualizado.apellidos,
                        'email': hermano_actualizado.email or '',
                    }
                )
                if created:
                    usuario.set_password(username)
                    usuario.save()
                
                from .models import Perfil
                perfil_usuario, perfil_created = Perfil.objects.get_or_create(
                    user=usuario,
                    cofradia=hermano_actualizado.cofradia,
                    defaults={'rol': 'hermano'}
                )
                
                hermano_actualizado.user = usuario
            else:
                # Si se elimina el DNI, desasociar usuario y opcionalmente eliminar perfil
                if hermano_actualizado.user:
                    # Opcional: eliminar perfil asociado a esta cofradía y usuario
                    from .models import Perfil
                    Perfil.objects.filter(user=hermano_actualizado.user, cofradia=hermano_actualizado.cofradia).delete()
                    hermano_actualizado.user = None
            
            hermano_actualizado.save()
            messages.success(request, 'Hermano actualizado correctamente.')
            return redirect('gestion_cofradia:ver_hermano', pk=hermano.pk)
    else:
        form = HermanoForm(instance=hermano)
    
    return render(request, 'hermanos/editar_hermano.html', {'form': form, 'hermano': hermano})

@login_required
@role_required(roles_permitidos=['secretario', 'tesorero', 'hermano_mayor'])
def notificar_hermano(request, pk):
    perfil = request.user.perfil_set.first()
    if not perfil:
        return redirect('gestion_cofradia:login')
    cofradia_usuario = perfil.cofradia
    hermano = get_object_or_404(Hermano, pk=pk, cofradia=cofradia_usuario)

    if request.method == 'POST':
        form = NotificacionForm(request.POST, cofradia=cofradia_usuario)
        if form.is_valid():
            notificacion = form.save(commit=False)
            notificacion.cofradia = cofradia_usuario
            notificacion.destinatario = hermano
            notificacion.fecha_envio = timezone.now()
            notificacion.save()

            messages.success(request, f'Notificación creada para {hermano.nombre} {hermano.apellidos}.')
            return redirect('gestion_cofradia:ver_hermano', pk=pk)
    else:
        form = NotificacionForm(
            initial={
                'destinatario': hermano,
                'titulo': f'Notificación de {hermano.cofradia.nombre}',
                'cuerpo': f'Estimado/a {hermano.nombre} {hermano.apellidos},\n\n',
            },
            cofradia=cofradia_usuario
        )

    return render(request, 'notificaciones/notificar_hermano.html', {
        'hermano': hermano,
        'form': form,
    })

@login_required
@role_required(roles_permitidos=['secretario', 'tesorero', 'hermano_mayor'])
def upload_hermanos_csv(request):
    perfil = request.user.perfil_set.first()
    if not perfil:
        return redirect('gestion_cofradia:login')
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        
        # Usar la codificación latin-1
        try:
            decoded_file = csv_file.read().decode('latin-1').splitlines()
            reader = csv.DictReader(decoded_file, delimiter=';')
        except UnicodeDecodeError:
            messages.error(request, "No se pudo decodificar el archivo CSV. Asegúrate de que está guardado en latin-1.")
            return render(request, 'hermanos/upload_csv.html')

        cofradia = perfil.cofradia
        
        # Generar el hash de la contraseña temporal UNA SOLA VEZ
        hashed_default_password = make_password("Temporal01")

        for row in reader:
            try:
                num_hermano = int(row['ID']) if row['ID'] else None
                dni = row['DNI'].strip() if row['DNI'] else None
                nombre = row['NOMBRE'].strip() if row['NOMBRE'] else ''
                apellidos = row['APELLIDOS'].strip() if row['APELLIDOS'] else ''
                telefono = row['TELEFONO'].strip() if row['TELEFONO'] else None
                direccion = row['DIRECCION'].strip() if row['DIRECCION'] else ''
                localidad = row['LOCALIDAD'].strip() if row['LOCALIDAD'] else ''
                fecha_nacimiento = row['FECHA_NACIMIENTO'].strip() if row['FECHA_NACIMIENTO'] else None
                fecha_inicio = row['FECHA_INICIO'].strip() if row['FECHA_INICIO'] else None
                fecha_ultimo_pago = row['FECHA_ULTIMO_PAGO'].strip() if row['FECHA_ULTIMO_PAGO'] else None
                estado_nombre = row['ESTADO'].strip() if row['ESTADO'] else None
                forma_pago_nombre = row['FORMA_PAGO'].strip() if row['FORMA_PAGO'] else ''
                forma_comunicacion_nombre = row['FORMA_COMUNICACION'].strip() if row['FORMA_COMUNICACION'] else ''
                email = row['EMAIL'].strip() if row['EMAIL'] else ''
                iban = row['IBAN'].strip() if row['IBAN'] else ''

                # Manejo de fechas
                from datetime import datetime
                try:
                    fecha_nacimiento = datetime.strptime(fecha_nacimiento, '%d/%m/%Y').date() if fecha_nacimiento else None
                except ValueError:
                    fecha_nacimiento = None
                try:
                    fecha_inicio_cofradia = int(fecha_inicio) if fecha_inicio else None
                except ValueError:
                    fecha_inicio_cofradia = None
                try:
                    fecha_ultimo_pago_int = int(fecha_ultimo_pago) if fecha_ultimo_pago else None
                except ValueError:
                    fecha_ultimo_pago_int = None

                # ForeignKeys
                forma_pago = None
                if forma_pago_nombre:
                    forma_pago, _ = FormaPago.objects.get_or_create(nombre=forma_pago_nombre)
                forma_comunicacion = None
                if forma_comunicacion_nombre:
                    forma_comunicacion, _ = FormaComunicacion.objects.get_or_create(nombre=forma_comunicacion_nombre)
                
                # Estado como tabla maestra
                estado = None
                if estado_nombre:
                    estado, _ = EstadoHermano.objects.get_or_create(nombre=estado_nombre)

                # Usuario asociado solo si hay DNI
                user = None
                if dni:
                    user, created = User.objects.get_or_create(
                        username=dni,  # Username sigue siendo el DNI
                        defaults={'email': email, 'first_name': nombre, 'last_name': apellidos}
                    )
                    if created:
                        # Asignar la contraseña temporal ya hasheada
                        user.password = hashed_default_password
                        user.save()
                        
                        # Crear perfil asociado al usuario
                        from .models import Perfil  # Asegúrate de importar el modelo Perfil
                        Perfil.objects.create(
                            user=user,
                            cofradia=cofradia,
                            rol='hermano'
                        )

                hermano, created = Hermano.objects.get_or_create(
                    cofradia=cofradia,
                    num_hermano=num_hermano,
                    defaults={
                        'dni': dni,
                        'user': user,
                        'nombre': nombre,
                        'apellidos': apellidos,
                        'telefono': telefono,
                        'direccion': direccion,
                        'localidad': localidad,
                        'fecha_nacimiento': fecha_nacimiento,
                        'fecha_inicio_cofradia': fecha_inicio_cofradia,
                        'fecha_ultimo_pago': fecha_ultimo_pago_int,
                        'estado': estado,
                        'forma_pago': forma_pago,
                        'forma_comunicacion': forma_comunicacion,
                        'email': email,
                        'rol': 'hermano',
                        'iban': iban,
                    }
                )
                if not created:
                    # Si ya existe, puedes actualizar los datos si lo deseas
                    pass

            except Exception as e:
                messages.error(request, f"Error en la fila {row}: {e}")

        messages.success(request, "Importación completada.")
        return redirect('gestion_cofradia:lista_hermanos')

    return render(request, 'hermanos/upload_csv.html')


#CUOTAS
@login_required
@role_required(roles_permitidos=['secretario', 'tesorero', 'hermano_mayor'])
def lista_cuotas(request):
    perfil = request.user.perfil_set.first()
    if not perfil:
        return redirect('gestion_cofradia:login')
    cofradia = perfil.cofradia
    cuotas = Cuota.objects.filter(cofradia=cofradia)
    return render(request, 'cuotas/lista_cuotas.html', {'cuotas': cuotas})

@login_required
@role_required(roles_permitidos=['secretario', 'tesorero', 'hermano_mayor'])
def crear_cuota(request):
    perfil = request.user.perfil_set.first()
    if not perfil:
        return redirect('gestion_cofradia:login')
    cofradia = perfil.cofradia
    if request.method == 'POST':
        form = CuotaForm(request.POST)
        if form.is_valid():
            cuota = form.save(commit=False)
            cuota.cofradia = cofradia
            cuota.save()

            if cuota.tipo == 'anual':
                estado_activo = EstadoHermano.objects.get(nombre='Activo')
                estado_no_pagado = EstadoHermano.objects.get(nombre='No Pagado')
                Hermano.objects.filter(cofradia=cofradia, estado=estado_activo).update(estado=estado_no_pagado)

            hermanos = Hermano.objects.filter(cofradia=cofradia)
            for hermano in hermanos:
                if hermano.user and hermano.user.email:
                    notificacion = Notificacion.objects.create(
                        cofradia=cofradia,
                        destinatario=hermano.user,
                        titulo=f"Nueva cuota disponible: {cuota}",
                        cuerpo=f"Ya está disponible la cuota {cuota}. Puedes gestionarla desde tu área personal.",
                        tipo='cuota'
                    )
                    # Enviar email
                    subject = f"Nueva notificación: {notificacion.titulo}"
                    message = f"Hola {hermano.nombre},\n\n{notificacion.cuerpo}\n\nPor favor, accede al portal para más detalles."
                    from_email = settings.DEFAULT_FROM_EMAIL
                    recipient_list = [hermano.user.email]
                    send_mail(subject, message, from_email, recipient_list)

            messages.success(request, "Cuota creada y notificaciones enviadas.")
            return redirect('gestion_cofradia:lista_cuotas')
    else:
        form = CuotaForm()
    return render(request, 'cuotas/crear_cuota.html', {'form': form})

@login_required
@role_required(roles_permitidos=['secretario', 'tesorero', 'hermano_mayor'])
def editar_cuota(request, pk):
    perfil = request.user.perfil_set.first()
    if not perfil:
        return redirect('gestion_cofradia:login')
    cofradia = perfil.cofradia
    cuota = get_object_or_404(Cuota, pk=pk, cofradia=cofradia)
    if request.method == 'POST':
        form = CuotaForm(request.POST, instance=cuota)
        if form.is_valid():
            form.save()
            return redirect('gestion_cofradia:lista_cuotas')
    else:
        form = CuotaForm(instance=cuota)
    return render(request, 'cuotas/editar_cuota.html', {'form': form, 'cuota': cuota})

@login_required
@role_required(roles_permitidos=['secretario', 'tesorero', 'hermano_mayor'])
def eliminar_cuota(request, pk):
    perfil = request.user.perfil_set.first()
    if not perfil:
        return redirect('gestion_cofradia:login')
    cofradia = perfil.cofradia
    cuota = get_object_or_404(Cuota, pk=pk, cofradia=cofradia)
    if request.method == 'POST':
        cuota.delete()
        return redirect('gestion_cofradia:lista_cuotas')
    return render(request, 'cuotas/eliminar_cuota.html', {'cuota': cuota})


#PAGOS
@login_required
@role_required(roles_permitidos=['secretario', 'tesorero', 'hermano_mayor'])
def registrar_pago(request, hermano_pk, cuota_pk):
    perfil = request.user.perfil_set.first()
    if not perfil:
        return redirect('gestion_cofradia:login')
    cofradia = perfil.cofradia
    hermano = get_object_or_404(Hermano, pk=hermano_pk, cofradia=cofradia)
    cuota = get_object_or_404(Cuota, pk=cuota_pk, cofradia=cofradia)

    if request.method == 'POST':
        form = PagoForm(request.POST)
        if form.is_valid():
            pago = form.save(commit=False)
            pago.cofradia = cofradia
            pago.hermano = hermano
            pago.cuota = cuota
            pago.registrado_por = request.user
            pago.save()

            # Verificar si tiene más cuotas pendientes
            cuotas_pendientes = Cuota.objects.filter(
                cofradia=cofradia,
                activa=True
            ).exclude(
                pagos__hermano=hermano
            )

            if not cuotas_pendientes.exists():
                estado_activo = EstadoHermano.objects.get(nombre='Activo')
                hermano.estado = estado_activo
                hermano.fecha_ultimo_pago = timezone.now().year  # Obtiene el año actual
                hermano.save()

            return redirect('gestion_cofradia:ver_hermano', pk=hermano.pk)
    else:
        form = PagoForm(initial={'fecha_pago': timezone.now().date()})

    return render(request, 'pagos/registrar_pago.html', {'form': form, 'hermano': hermano, 'cuota': cuota})

@login_required
@role_required(roles_permitidos=['secretario', 'tesorero', 'hermano_mayor'])
def lista_pagos_hermano(request, hermano_pk):
    perfil = request.user.perfil_set.first()
    if not perfil:
        return redirect('gestion_cofradia:login')
    cofradia = perfil.cofradia
    hermano = get_object_or_404(Hermano, pk=hermano_pk, cofradia=cofradia)
    pagos = Pago.objects.filter(hermano=hermano)
    return render(request, 'pagos/lista_pagos_hermano.html', {'pagos': pagos, 'hermano': hermano})


#NOTIFICACIONES
@login_required
@role_required(roles_permitidos=['secretario', 'tesorero', 'hermano_mayor'])
def lista_notificaciones(request):
    perfil = request.user.perfil_set.first()
    if not perfil:
        return redirect('gestion_cofradia:login')
    notificaciones = Notificacion.objects.all()
    return render(request, 'notificaciones/lista_notificaciones.html', {'notificaciones': notificaciones})

@login_required
@role_required(roles_permitidos=['secretario', 'tesorero', 'hermano_mayor'])
def crear_notificacion(request):
    perfil = request.user.perfil_set.first()
    if not perfil:
        return redirect('gestion_cofradia:login')
    cofradia = perfil.cofradia

    if request.method == 'POST':
        form = NotificacionForm(request.POST, cofradia=cofradia)
        if form.is_valid():
            notificacion = form.save(commit=False)
            notificacion.cofradia = cofradia
            notificacion.save()

            # Enviar email de aviso
            if notificacion.destinatario and notificacion.destinatario.email:
                subject = f"Nueva notificación: {notificacion.titulo}"
                message = f"Tienes una nueva notificación en el portal de la cofradía {cofradia.nombre}.\n\nTítulo: {notificacion.titulo}\n\nPor favor, accede al portal para más detalles."
                from_email = settings.DEFAULT_FROM_EMAIL
                recipient_list = [notificacion.destinatario.email]
                send_mail(subject, message, from_email, recipient_list)

            return redirect('gestion_cofradia:lista_notificaciones')
    else:
        form = NotificacionForm(cofradia=cofradia)

    return render(request, 'notificaciones/crear_notificacion.html', {'form': form, 'cofradia': cofradia})

@login_required
@role_required(roles_permitidos=['secretario', 'tesorero', 'hermano_mayor'])
def ver_notificacion(request, pk):
    perfil = request.user.perfil_set.first()
    if not perfil:
        return redirect('gestion_cofradia:login')
    notificacion = get_object_or_404(Notificacion, pk=pk)
    return render(request, 'notificaciones/ver_notificacion.html', {'notificacion': notificacion})

@login_required
@role_required(roles_permitidos=['secretario', 'tesorero', 'hermano_mayor'])
def editar_notificacion(request, pk):
    perfil = request.user.perfil_set.first()
    if not perfil:
        return redirect('gestion_cofradia:login')
    notificacion = get_object_or_404(Notificacion, pk=pk)
    if request.method == 'POST':
        form = NotificacionForm(request.POST, instance=notificacion)
        if form.is_valid():
            form.save()
            return redirect('gestion_cofradia:ver_notificacion', pk=notificacion.pk)
    else:
        form = NotificacionForm(instance=notificacion)
    return render(request, 'notificaciones/editar_notificacion.html', {'form': form, 'notificacion': notificacion})

@login_required
@role_required(roles_permitidos=['secretario', 'tesorero', 'hermano_mayor'])
def eliminar_notificacion(request, pk):
    perfil = request.user.perfil_set.first()
    if not perfil:
        return redirect('gestion_cofradia:login')
    notificacion = get_object_or_404(Notificacion, pk=pk)

    if request.method == 'POST':
        titulo_notificacion = notificacion.titulo
        notificacion.delete()
        messages.success(request, f'La notificación "{titulo_notificacion}" ha sido eliminada correctamente.')
        return redirect('gestion_cofradia:lista_notificaciones')

    return render(request, 'notificaciones/eliminar_notificacion.html', {'notificacion': notificacion})


#TAREAS
@login_required
@role_required(roles_permitidos=['secretario', 'tesorero', 'hermano_mayor'])
def lista_tareas(request):
    perfil = request.user.perfil_set.first()
    if not perfil:
        return redirect('gestion_cofradia:login')
    tareas_pendientes = Tarea.objects.filter(estado__in=['pendiente', 'en_progreso']).order_by('fecha_limite')
    tareas_completadas = Tarea.objects.filter(estado='completada').order_by('-fecha_completada')
    return render(request, 'tareas/lista_tareas.html', {
        'tareas_pendientes': tareas_pendientes,
        'tareas_completadas': tareas_completadas,
    })

@login_required
@role_required(roles_permitidos=['secretario', 'tesorero', 'hermano_mayor'])
def crear_tarea(request):
    perfil = request.user.perfil_set.first()
    if not perfil:
        return redirect('gestion_cofradia:login')
    if request.method == 'POST':
        form = TareaForm(request.POST)
        if form.is_valid():
            tarea = form.save(commit=False)
            # Asigna la cofradía del usuario logueado
            tarea.cofradia = perfil.cofradia
            tarea.save()
            return redirect('gestion_cofradia:lista_tareas')
    else:
        form = TareaForm()
    return render(request, 'tareas/crear_tarea.html', {'form': form})

@login_required
@role_required(roles_permitidos=['secretario', 'tesorero', 'hermano_mayor'])
def ver_tarea(request, pk):
    perfil = request.user.perfil_set.first()
    if not perfil:
        return redirect('gestion_cofradia:login')
    tarea = get_object_or_404(Tarea, pk=pk)
    return render(request, 'gestion_cofradia/ver_tarea.html', {'tarea': tarea})

@login_required
@role_required(roles_permitidos=['secretario', 'tesorero', 'hermano_mayor'])
def editar_tarea(request, tarea_id):
    perfil = request.user.perfil_set.first()
    if not perfil:
        return redirect('gestion_cofradia:login')
    tarea = get_object_or_404(Tarea, id=tarea_id)
    if request.method == 'POST':
        form = TareaForm(request.POST, instance=tarea)
        if form.is_valid():
            form.save()
            return redirect('gestion_cofradia:lista_tareas')
    else:
        form = TareaForm(instance=tarea)
    return render(request, 'tareas/editar_tarea.html', {'form': form, 'tarea': tarea})

@login_required
@role_required(roles_permitidos=['secretario', 'tesorero', 'hermano_mayor'])
def completar_tarea(request, tarea_id):
    perfil = request.user.perfil_set.first()
    if not perfil:
        return redirect('gestion_cofradia:login')
    tarea = get_object_or_404(Tarea, id=tarea_id)
    tarea.estado = 'completada'
    tarea.fecha_completada = timezone.now()
    tarea.save()
    return redirect('gestion_cofradia:lista_tareas')


#DOCUMENTACION
@login_required
@role_required(roles_permitidos=['secretario', 'tesorero', 'hermano_mayor'])
def lista_documentos(request):
    perfil = request.user.perfil_set.first()
    if not perfil:
        return redirect('gestion_cofradia:login')
    cofradia = perfil.cofradia
    documentos = Documento.objects.filter(cofradia=cofradia).order_by('-fecha_subida')
    return render(request, 'documentos/lista_documentos.html', {'documentos': documentos})

@login_required
@role_required(roles_permitidos=['secretario', 'tesorero', 'hermano_mayor'])
def crear_documento(request):
    perfil = request.user.perfil_set.first()
    if not perfil:
        return redirect('gestion_cofradia:login')
    cofradia = perfil.cofradia
    if request.method == 'POST':
        form = DocumentoForm(request.POST, request.FILES)
        if form.is_valid():
            documento = form.save(commit=False)
            documento.cofradia = cofradia
            documento.subido_por = request.user
            documento.save()
            return redirect('gestion_cofradia:lista_documentos')
    else:
        form = DocumentoForm()
    return render(request, 'documentos/crear_documento.html', {'form': form})

@login_required
@role_required(roles_permitidos=['secretario', 'tesorero', 'hermano_mayor'])
def ver_documento(request, documento_id):
    perfil = request.user.perfil_set.first()
    if not perfil:
        return redirect('gestion_cofradia:login')
    documento = get_object_or_404(Documento, pk=documento_id, cofradia=perfil.cofradia)
    return render(request, 'documentos/ver_documento.html', {'documento': documento})

@login_required
@role_required(roles_permitidos=['secretario', 'tesorero', 'hermano_mayor'])
def editar_documento(request, documento_id):
    perfil = request.user.perfil_set.first()
    if not perfil:
        return redirect('gestion_cofradia:login')
    documento = get_object_or_404(Documento, pk=documento_id, cofradia=perfil.cofradia)
    if request.method == 'POST':
        form = DocumentoForm(request.POST, request.FILES, instance=documento)
        if form.is_valid():
            form.save()
            return redirect('gestion_cofradia:lista_documentos')
    else:
        form = DocumentoForm(instance=documento)
    return render(request, 'documentos/editar_documento.html', {'form': form, 'documento': documento})

@login_required
@role_required(roles_permitidos=['secretario', 'tesorero', 'hermano_mayor'])
def eliminar_documento(request, documento_id):
    perfil = request.user.perfil_set.first()
    if not perfil:
        return redirect('gestion_cofradia:login')
    documento = get_object_or_404(Documento, pk=documento_id, cofradia=perfil.cofradia)
    if request.method == 'POST':
        documento.delete()
        return redirect('gestion_cofradia:lista_documentos')
    return render(request, 'documentos/eliminar_documento.html', {'documento': documento})


#INFORMES
@login_required
@role_required(roles_permitidos=['secretario', 'tesorero', 'hermano_mayor'])
def lista_informes(request):
    return render(request, 'documentos/informes/lista_informes.html')

@login_required
@role_required(roles_permitidos=['secretario', 'tesorero', 'hermano_mayor'])
def descargar_informe(request, tipo):
    perfil = request.user.perfil_set.first()
    if not perfil:
        return redirect('gestion_cofradia:login')
    print("DEBUG - perfil:", perfil)
    print("DEBUG - perfil Cofradía:", perfil.cofradia)
    cofradia = perfil.cofradia

    if tipo == 'hermanos_activos_mayores':
        return generar_pdf_hermanos_activos_mayores(cofradia)

    elif tipo == 'hermanos_carta_postal':
        return generar_pdf_hermanos_carta_postal(cofradia)

    else:
        return HttpResponse("Informe no encontrado", status=404)

def generar_pdf_hermanos_activos_mayores(cofradia):
    hoy = now().date()
    edad_mayor = 18
    fecha_limite = hoy - timedelta(days=edad_mayor * 365.25)

    # Hermanos activos mayores de edad con DNI
    hermanos_activos_con_dni = cofradia.hermanos.filter(
        estado__nombre__iexact='activo',
        dni__isnull=False,
        dni__gt='',
        fecha_nacimiento__isnull=False,
        fecha_nacimiento__lte=fecha_limite
    ).order_by('apellidos', 'nombre')

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter),
                            rightMargin=40, leftMargin=40,
                            topMargin=60, bottomMargin=40)

    styles = getSampleStyleSheet()
    style_title = ParagraphStyle(
        name='Title',
        fontSize=18,
        leading=22,
        alignment=TA_CENTER,
        spaceAfter=20,
        fontName='Helvetica-Bold'
    )
    style_normal = styles['Normal']

    title = Paragraph(f"Hermanos mayores de {edad_mayor} años - Cofradía {cofradia.nombre}", style_title)
    fecha = Paragraph(f"Fecha de generación: {hoy.strftime('%d/%m/%Y')}", style_normal)

    # Tabla: Hermanos activos con DNI
    data = [['#', 'Apellidos', 'Nombre', 'DNI', 'Edad']]
    for i, h in enumerate(hermanos_activos_con_dni, start=1):
        edad = hoy.year - h.fecha_nacimiento.year - ((hoy.month, hoy.day) < (h.fecha_nacimiento.month, h.fecha_nacimiento.day))
        data.append([str(i), h.apellidos or '', h.nombre or '', h.dni or '', str(edad)])

    total = len(hermanos_activos_con_dni)
    porcentaje = ceil(total * 0.2)
    data.append(['', '', '', 'Total:', str(total)])
    data.append(['', '', '', '20% redondeado:', str(porcentaje)])

    table = Table(data, colWidths=[0.5*inch, 2.5*inch, 2*inch, 1.5*inch, 0.7*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightblue),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 12),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('BACKGROUND', (0,1), (-1,-3), colors.whitesmoke),
        ('BACKGROUND', (0,-2), (-1,-1), colors.lightgrey),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
    ]))

    elements = [
        title,
        fecha,
        Spacer(1, 12),
        Paragraph("Hermanos activos con DNI y mayores de edad", style_normal),
        table,
    ]

    doc.build(elements)

    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="hermanos_mayores.pdf"'
    return response

def generar_pdf_hermanos_carta_postal(cofradia):
    hoy = now().date()

    hermanos = cofradia.hermanos.filter(
        estado__nombre__iexact='activo',
        forma_comunicacion__nombre__iexact='carta postal'
    ).order_by('localidad', 'direccion', 'apellidos')

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter),
                            rightMargin=40, leftMargin=40,
                            topMargin=60, bottomMargin=40)

    styles = getSampleStyleSheet()
    style_title = ParagraphStyle(
        name='Title',
        fontSize=18,
        leading=22,
        alignment=TA_CENTER,
        spaceAfter=20,
        fontName='Helvetica-Bold'
    )
    style_normal = styles['Normal']

    title = Paragraph(f"Hermanos con forma de comunicación 'Carta Postal' - Cofradía {cofradia.nombre}", style_title)
    fecha = Paragraph(f"Fecha de generación: {hoy.strftime('%d/%m/%Y')}", style_normal)

    data = [['Apellidos', 'Nombre', 'Teléfono', 'Localidad', 'Dirección']]
    for h in hermanos:
        telefono = h.telefono or 'No disponible'
        localidad = h.localidad or 'No disponible'
        direccion = h.direccion or 'No disponible'
        data.append([h.apellidos or '', h.nombre or '', telefono, localidad, direccion])

    table = Table(data, colWidths=[2.1*inch, 1.8*inch, 1*inch, 2.5*inch, 3*inch])
    table_style = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightblue),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 12),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('BACKGROUND', (0,1), (-1,-1), colors.whitesmoke),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
    ])
    table.setStyle(table_style)

    elements = [title, fecha, Spacer(1, 12), table]
    doc.build(elements)

    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="hermanos_carta_postal.pdf"'
    return response


# EVENTOS
@login_required
@role_required(roles_permitidos=['secretario', 'tesorero', 'hermano_mayor'])
def lista_eventos(request):
    perfil = request.user.perfil_set.first()
    if not perfil:
        return redirect('gestion_cofradia:login')
    cofradia = perfil.cofradia
    eventos = Evento.objects.filter(cofradia=cofradia).order_by('-fecha')
    return render(request, 'eventos/lista_eventos.html', {'eventos': eventos})

@login_required
@role_required(roles_permitidos=['secretario', 'tesorero', 'hermano_mayor'])
def crear_evento(request):
    perfil = request.user.perfil_set.first()
    if not perfil:
        return redirect('gestion_cofradia:login')
    cofradia = perfil.cofradia

    if request.method == 'POST':
        form = EventoForm(request.POST, cofradia=cofradia)
        if form.is_valid():
            evento = form.save(commit=False)
            evento.cofradia = cofradia
            evento.save()

            if evento.tipo == 'reunion':
                hoy = evento.fecha.date()
                edad_mayor = 18
                fecha_limite = hoy - timedelta(days=edad_mayor * 365.25)

                # Hermanos activos, con DNI, con fecha nacimiento y mayores de edad
                hermanos_primera_tabla = cofradia.hermanos.filter(
                    estado__nombre__iexact='activo',
                    dni__isnull=False,
                    dni__gt='',
                    fecha_nacimiento__isnull=False,
                    fecha_nacimiento__lte=fecha_limite
                ).order_by('apellidos', 'nombre')

                buffer = BytesIO()
                doc = SimpleDocTemplate(buffer, pagesize=landscape(letter),
                                        rightMargin=40, leftMargin=40,
                                        topMargin=60, bottomMargin=40)

                styles = getSampleStyleSheet()
                style_title = ParagraphStyle(
                    name='Title',
                    fontSize=18,
                    leading=22,
                    alignment=TA_CENTER,
                    spaceAfter=20,
                    fontName='Helvetica-Bold'
                )
                style_normal = styles['Normal']

                title = Paragraph(f"Hermanos mayores de {edad_mayor} años para la reunión: {evento.nombre}", style_title)
                fecha = Paragraph(f"Fecha del evento: {evento.fecha.strftime('%d/%m/%Y %H:%M')}", style_normal)

                # Tabla: hermanos que cumplen condiciones
                data1 = [['#', 'Apellidos', 'Nombre', 'DNI', 'Edad']]
                for i, h in enumerate(hermanos_primera_tabla, start=1):
                    edad = hoy.year - h.fecha_nacimiento.year - ((hoy.month, hoy.day) < (h.fecha_nacimiento.month, h.fecha_nacimiento.day))
                    data1.append([str(i), h.apellidos or '', h.nombre or '', h.dni or '', str(edad)])

                total1 = len(hermanos_primera_tabla)
                porcentaje1 = ceil(total1 * 0.2)
                data1.append(['', '', '', 'Total:', str(total1)])
                data1.append(['', '', '', '20% redondeado:', str(porcentaje1)])

                table1 = Table(data1, colWidths=[0.5*inch, 2.5*inch, 2*inch, 1.5*inch, 0.7*inch])
                table1.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.lightblue),
                    ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0,0), (-1,0), 12),
                    ('BOTTOMPADDING', (0,0), (-1,0), 8),
                    ('BACKGROUND', (0,1), (-1,-1), colors.whitesmoke),
                    ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ]))

                elements = [
                    title,
                    fecha,
                    Spacer(1, 12),
                    Paragraph("Hermanos activos, con DNI y mayores de edad", style_normal),
                    table1,
                ]

                doc.build(elements)

                buffer.seek(0)
                return FileResponse(buffer, as_attachment=True, filename=f"hermanos_reunion_{evento.id}.pdf")

            messages.success(request, f'Evento "{evento.nombre}" creado exitosamente.')
            return redirect('gestion_cofradia:lista_eventos')
    else:
        form = EventoForm(cofradia=cofradia)

    return render(request, 'eventos/crear_evento.html', {'form': form})

@login_required
@role_required(roles_permitidos=['secretario', 'tesorero', 'hermano_mayor'])
def ver_evento(request, evento_id):
    perfil = request.user.perfil_set.first()
    if not perfil:
        return redirect('gestion_cofradia:login')
    evento = get_object_or_404(Evento, pk=evento_id, cofradia=perfil.cofradia)
    return render(request, 'eventos/ver_evento.html', {'evento': evento})

@login_required
@role_required(roles_permitidos=['secretario', 'tesorero', 'hermano_mayor'])
def editar_evento(request, evento_id):
    perfil = request.user.perfil_set.first()
    if not perfil:
        return redirect('gestion_cofradia:login')
    evento = get_object_or_404(Evento, pk=evento_id, cofradia=perfil.cofradia)
    cofradia = perfil.cofradia
    
    if request.method == 'POST':
        form = EventoForm(request.POST, instance=evento, cofradia=cofradia)
        if form.is_valid():
            form.save()
            messages.success(request, f'Evento "{evento.nombre}" actualizado exitosamente.')
            return redirect('gestion_cofradia:ver_evento', evento_id=evento.id)
    else:
        form = EventoForm(instance=evento, cofradia=cofradia)
    return render(request, 'eventos/editar_evento.html', {'form': form, 'evento': evento})

@login_required
@role_required(roles_permitidos=['secretario', 'tesorero', 'hermano_mayor'])
def eliminar_evento(request, evento_id):
    perfil = request.user.perfil_set.first()
    if not perfil:
        return redirect('gestion_cofradia:login')
    evento = get_object_or_404(Evento, pk=evento_id, cofradia=perfil.cofradia)
    
    if request.method == 'POST':
        nombre_evento = evento.nombre
        evento.delete()
        messages.success(request, f'Evento "{nombre_evento}" eliminado exitosamente.')
        return redirect('gestion_cofradia:lista_eventos')
    
    return render(request, 'eventos/eliminar_evento.html', {'evento': evento})


#Alquileres
@login_required
@role_required(roles_permitidos=['secretario', 'tesorero', 'hermano_mayor'])
def lista_alquileres(request):
    perfil = request.user.perfil_set.first()
    if not perfil:
        return redirect('gestion_cofradia:login')
    cofradia = perfil.cofradia
    alquileres = Alquiler.objects.filter(cofradia=cofradia).select_related('enser', 'hermano', 'evento').order_by('-fecha_entrega')
    return render(request, 'alquileres/lista_alquileres.html', {'alquileres': alquileres})

@login_required
@role_required(roles_permitidos=['secretario', 'tesorero', 'hermano_mayor'])
def ver_alquiler(request, pk):
    perfil = request.user.perfil_set.first()
    if not perfil:
        return redirect('gestion_cofradia:login')
    cofradia = perfil.cofradia
    alquiler = get_object_or_404(Alquiler, pk=pk, cofradia=cofradia)
    return render(request, 'alquileres/ver_alquiler.html', {'alquiler': alquiler})

@login_required
@role_required(roles_permitidos=['secretario', 'tesorero', 'hermano_mayor'])
def crear_alquiler(request):
    perfil = request.user.perfil_set.first()
    if not perfil:
        return redirect('gestion_cofradia:login')
    cofradia = perfil.cofradia
    if request.method == 'POST':
        form = AlquilerForm(request.POST)
        if form.is_valid():
            alquiler = form.save(commit=False)
            alquiler.cofradia = cofradia
            alquiler.save()
            messages.success(request, 'Alquiler creado correctamente.')
            return redirect('gestion_cofradia:lista_alquileres')
    else:
        form = AlquilerForm()
    return render(request, 'alquileres/crear_alquiler.html', {'form': form})

@login_required
@role_required(roles_permitidos=['secretario', 'tesorero', 'hermano_mayor'])
def editar_alquiler(request, pk):
    perfil = request.user.perfil_set.first()
    if not perfil:
        return redirect('gestion_cofradia:login')
    cofradia = perfil.cofradia
    alquiler = get_object_or_404(Alquiler, pk=pk, cofradia=cofradia)
    if request.method == 'POST':
        form = AlquilerForm(request.POST, instance=alquiler)
        if form.is_valid():
            form.save()
            messages.success(request, 'Alquiler actualizado correctamente.')
            return redirect('gestion_cofradia:ver_alquiler', pk=alquiler.pk)
    else:
        form = AlquilerForm(instance=alquiler)
    return render(request, 'alquileres/editar_alquiler.html', {'form': form, 'alquiler': alquiler})

@login_required
@role_required(roles_permitidos=['secretario', 'tesorero', 'hermano_mayor'])
def eliminar_alquiler(request, pk):
    perfil = request.user.perfil_set.first()
    if not perfil:
        return redirect('gestion_cofradia:login')
    cofradia = perfil.cofradia
    alquiler = get_object_or_404(Alquiler, pk=pk, cofradia=cofradia)
    if request.method == 'POST':
        alquiler.delete()
        messages.success(request, 'Alquiler eliminado correctamente.')
        return redirect('gestion_cofradia:lista_alquileres')
    return render(request, 'alquileres/eliminar_alquiler.html', {'alquiler': alquiler})


#ENSERES
@login_required
@role_required(roles_permitidos=['secretario', 'tesorero', 'hermano_mayor'])
def lista_enseres(request):
    perfil = request.user.perfil_set.first()
    if not perfil:
        return redirect('gestion_cofradia:login')
    cofradia = perfil.cofradia

    ensers = Enser.objects.filter(cofradia=cofradia).order_by('nombre')
    return render(request, 'enseres/lista_enseres.html', {'ensers': ensers})

@login_required
@role_required(roles_permitidos=['secretario', 'tesorero', 'hermano_mayor'])
def ver_enser(request, pk):
    perfil = request.user.perfil_set.first()
    if not perfil:
        return redirect('gestion_cofradia:login')
    cofradia = perfil.cofradia

    enser = get_object_or_404(Enser, pk=pk, cofradia=cofradia)
    return render(request, 'enseres/ver_enser.html', {'enser': enser})

@login_required
@role_required(roles_permitidos=['secretario', 'tesorero', 'hermano_mayor'])
def crear_enser(request):
    perfil = request.user.perfil_set.first()
    if not perfil:
        return redirect('gestion_cofradia:login')
    cofradia = perfil.cofradia

    if request.method == 'POST':
        form = EnserForm(request.POST)
        if form.is_valid():
            enser = form.save(commit=False)
            enser.cofradia = cofradia
            enser.save()
            messages.success(request, f'Enser "{enser.nombre}" creado correctamente.')
            return redirect('gestion_cofradia:lista_enseres')
    else:
        form = EnserForm()
    return render(request, 'enseres/crear_enser.html', {'form': form})

@login_required
@role_required(roles_permitidos=['secretario', 'tesorero', 'hermano_mayor'])
def editar_enser(request, pk):
    perfil = request.user.perfil_set.first()
    if not perfil:
        return redirect('gestion_cofradia:login')
    cofradia = perfil.cofradia

    enser = get_object_or_404(Enser, pk=pk, cofradia=cofradia)
    if request.method == 'POST':
        form = EnserForm(request.POST, instance=enser)
        if form.is_valid():
            form.save()
            messages.success(request, f'Enser "{enser.nombre}" actualizado correctamente.')
            return redirect('gestion_cofradia:lista_enseres')
    else:
        form = EnserForm(instance=enser)
    return render(request, 'enseres/editar_enser.html', {'form': form, 'enser': enser})

@login_required
@role_required(roles_permitidos=['secretario', 'tesorero', 'hermano_mayor'])
def borrar_enser(request, pk):
    perfil = request.user.perfil_set.first()
    if not perfil:
        return redirect('gestion_cofradia:login')
    cofradia = perfil.cofradia

    enser = get_object_or_404(Enser, pk=pk, cofradia=cofradia)
    if request.method == 'POST':
        enser.delete()
        messages.success(request, f'Enser "{enser.nombre}" borrado correctamente.')
        return redirect('gestion_cofradia:lista_enseres')
    return render(request, 'enseres/borrar_enser.html', {'enser': enser})
