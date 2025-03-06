from datetime import date, timedelta
from django.db import transaction
from django.db.models import Q, Sum
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.utils.timezone import now
from .forms import HermanoForm, EventoForm, TareaForm, EstadoForm, FormaPagoForm, FormaComunicacionForm, CofradiaForm, CargarExcelForm
from .models import PerfilUsuario, Cargo, Hermano, Estado, FormaPago, FormaComunicacion, Cofradia, Tarea, Evento, Finanza
import datetime
import pandas as pd


# Create your views here.
class CustomLoginView(LoginView):
    template_name = 'login.html'

def logout_view(request):
    logout(request)  # Cierra la sesión
    return redirect('login')  # Redirige al login o a otra página después del logout

@login_required
def inicio(request):
    try:
        perfil = PerfilUsuario.objects.get(usuario=request.user)
    except PerfilUsuario.DoesNotExist:
        return redirect('login')

    # Obtener los objetos de los estados
    activo_estado = Estado.objects.get(nombre='Activo')
    no_pagado_estado = Estado.objects.get(nombre='No Pagado')
    baja_estado = Estado.objects.get(nombre='Baja')
    fallecido_estado = Estado.objects.get(nombre='Fallecido')

    # Obtener los objetos de las formas de pago
    efectivo_pago = FormaPago.objects.get(nombre='Efectivo')
    transferencia_pago = FormaPago.objects.get(nombre='Transferencia')
    domiciliacion_pago = FormaPago.objects.get(nombre='Domiciliación')

    # Obtener los objetos de las formas de comunicación
    telefono_comunicacion = FormaComunicacion.objects.get(nombre='Whatsapp')
    carta_comunicacion = FormaComunicacion.objects.get(nombre='Carta Postal')
    email_comunicacion = FormaComunicacion.objects.get(nombre='Email')

    # Datos para los gráficos
    hermanos_total = Hermano.objects.count()
    hermanos_activos = Hermano.objects.filter(estado=activo_estado).count()
    hermanos_no_pagados = Hermano.objects.filter(estado=no_pagado_estado).count()
    hermanos_baja = Hermano.objects.filter(estado=baja_estado).count()
    hermanos_fallecidos = Hermano.objects.filter(estado=fallecido_estado).count()

    pago_efectivo = Hermano.objects.filter(forma_pago=efectivo_pago).count()
    pago_transferencia = Hermano.objects.filter(forma_pago=transferencia_pago).count()
    pago_domiciliacion = Hermano.objects.filter(forma_pago=domiciliacion_pago).count()

    comunicacion_telefono = Hermano.objects.filter(forma_comunicacion=telefono_comunicacion).count()
    comunicacion_carta = Hermano.objects.filter(forma_comunicacion=carta_comunicacion).count()
    comunicacion_email = Hermano.objects.filter(forma_comunicacion=email_comunicacion).count()

    # **Nuevos datos para el Dashboard**
    # Obtener la fecha actual
    hoy = timezone.now().date()
    limite_30_dias = hoy + timedelta(days=30)
    hoy_mas_5 = hoy + timezone.timedelta(days=5)

    tareas_proximas = Tarea.objects.filter(
        estado='Pendiente', 
        fecha_limite__range=[hoy, limite_30_dias]
    ).order_by('fecha_limite')
    # Tareas urgentes (menos de 5 días para vencimiento)
    tareas_urgentes = tareas_proximas.filter(fecha_limite__lte=hoy + timedelta(days=5))

    eventos_proximos = Evento.objects.filter(fecha__gte=now().date()).order_by('fecha')[:3]

    total_ingresos = Finanza.objects.filter(tipo='Ingreso').aggregate(Sum('monto'))['monto__sum'] or 0
    total_gastos = Finanza.objects.filter(tipo='Gasto').aggregate(Sum('monto'))['monto__sum'] or 0
    saldo_total = total_ingresos - total_gastos

    context = {
        'perfil': perfil,
        'hoy_mas_5': hoy_mas_5,
        'hermanos_total': hermanos_total or 0,
        'hermanos_activos': hermanos_activos or 0,
        'hermanos_no_pagados': hermanos_no_pagados or 0,
        'hermanos_baja': hermanos_baja or 0,
        'hermanos_fallecidos': hermanos_fallecidos or 0,
        'pago_efectivo': pago_efectivo or 0,
        'pago_transferencia': pago_transferencia or 0,
        'pago_domiciliacion': pago_domiciliacion or 0,
        'comunicacion_telefono': comunicacion_telefono or 0,
        'comunicacion_carta': comunicacion_carta or 0,
        'comunicacion_email': comunicacion_email or 0,
        'tareas_proximas': tareas_proximas,
        'tareas_urgentes': tareas_urgentes,
        'eventos_proximos': eventos_proximos,
        'total_ingresos': total_ingresos,
        'total_gastos': total_gastos,
        'saldo_total': saldo_total
    }

    return render(request, 'inicio.html', context)



#Hermanos
@login_required
def crear_hermano(request):
    if request.method == 'POST':
        form = HermanoForm(request.POST)

        if form.is_valid():

            perfil_usuario = PerfilUsuario.objects.get(usuario=request.user)

            hermano = form.save(commit=False)
            hermano.cofradia = perfil_usuario.cofradia
            hermano.save()

            # Crear usuario solo si hay DNI
            if hermano.dni and not User.objects.filter(username=hermano.dni).exists():
                user = User.objects.create_user(username=hermano.dni, password=hermano.dni, email=hermano.email)
                PerfilUsuario.objects.create(usuario=user, cofradia=perfil_usuario.cofradia, cargo=Cargo.objects.get_or_create(cargo='Hermano'))
                user.set_password(hermano.dni)  # Guardar contraseña de forma segura
                user.save()

            return redirect('lista_hermanos')
    else:
        form = HermanoForm()
    return render(request, 'crear_hermano.html', {'form': form})

@login_required
def lista_hermanos(request):
    # Obtener el parámetro de ordenación (por defecto será por 'id')
    order_by = request.GET.get('order_by', 'id')  # Si no se especifica, se ordena por 'id'
    valid_order_fields = ['id', 'dni', 'nombre', 'apellidos', 'telefono', 'direccion', 'localidad', 'fecha_nacimiento', 'estado']
    
    # Si el 'order_by' no está en los campos válidos, usar 'id' como valor por defecto
    if order_by not in valid_order_fields:
        order_by = 'id'  # Orden por defecto en caso de un parámetro no válido
    
    # Filtros
    estado_filter = request.GET.get('estado', '')
    apellidos_filter = request.GET.get('apellidos', '')

    # Consultar todos los hermanos
    hermanos = Hermano.objects.all()

    # Aplicar filtros
    if estado_filter:
        hermanos = hermanos.filter(estado__nombre=estado_filter)

    if apellidos_filter:
        hermanos = hermanos.filter(Q(nombre__icontains=apellidos_filter) | Q(apellidos__icontains=apellidos_filter))

    # Ordenar según el 'order_by'
    hermanos = hermanos.order_by(order_by)

    return render(request, 'lista_hermanos.html', {
        'hermanos': hermanos,
        'order_by': order_by,
        'estado_filter': estado_filter,
        'nombre_filter': apellidos_filter,
    })

login_required
def detalle_hermano(request, pk):
    hermano = get_object_or_404(Hermano, pk=pk)
    return render(request, 'detalle_hermano.html', {'hermano': hermano})

@login_required
def editar_hermano(request, pk):
    hermano = get_object_or_404(Hermano, pk=pk)

    if request.method == "POST":
        form = HermanoForm(request.POST, instance=hermano)
        if form.is_valid():
            hermano = form.save(commit=False)

            user = User.objects.filter(username=form.dni)
            user.email =form.email

            hermano.save()
            user.save()

            return redirect('listar_hermanos')
    else:
        form = HermanoForm(instance=hermano)

    return render(request, 'editar_hermano.html', {'form': form})

@login_required
def eliminar_hermano(request, pk):
    hermano = get_object_or_404(Hermano, pk=pk)
    if request.method == "POST":
        hermano.delete()
        return redirect('listar_hermanos')

    return render(request, 'eliminar_hermano.html', {'hermano': hermano})



#Tareas
@login_required
def crear_tarea(request):
    if request.method == 'POST':
        form = TareaForm(request.POST)
        if form.is_valid():

            perfil_usuario = PerfilUsuario.objects.get(usuario=request.user)
            tarea = form.save(commit=False)
            tarea.cofradia = perfil_usuario.cofradia  # Asignar la cofradía del usuario logueado
            tarea.save()
            return redirect('lista_tareas')
    else:
        form = TareaForm()
    return render(request, 'crear_tarea.html', {'form': form})

@login_required
def lista_tareas(request):
    # Obtener el parámetro de ordenación (por defecto será por 'id')
    order_by = request.GET.get('order_by', 'id')  # Si no se especifica, se ordena por 'id'
    valid_order_fields = ['id', 'titulo', 'descripcion', 'asignado_a', 'fecha_limite', 'estado', 'prioridad']
    
    # Si el 'order_by' no está en los campos válidos, usar 'id' como valor por defecto
    if order_by not in valid_order_fields:
        order_by = 'id'  # Orden por defecto en caso de un parámetro no válido
    
    # Filtros
    titulo_filter = request.GET.get('titulo', '')
    estado_filter = request.GET.get('estado', '')
    prioridad_filter = request.GET.get('estado', '')

    # Consultar todos los hermanos
    tareas = Tarea.objects.all()

    # Aplicar filtros
    if titulo_filter:
        tareas = tareas.filter(Q(titulo__icontains=titulo_filter))
    if estado_filter:
        tareas = tareas.filter(Q(estado__icontains=estado_filter))
    if prioridad_filter:
        tareas = tareas.filter(Q(prioridad__icontains=prioridad_filter))

    # Ordenar según el 'order_by'
    tareas = tareas.order_by(order_by)

    return render(request, 'lista_tareas.html', {
        'tareas': tareas,
        'order_by': order_by,
        'titulo_filter': titulo_filter,
        'estado_filter': estado_filter,
        'prioridad_filter': prioridad_filter,
    })

login_required
def detalle_tarea(request, pk):
    tarea = get_object_or_404(Tarea, pk=pk)
    return render(request, 'detalle_tarea.html', {'tarea': tarea})

@login_required
def editar_tarea(request, pk):
    tarea = get_object_or_404(Tarea, pk=pk)

    if request.method == "POST":
        form = TareaForm(request.POST, instance=tarea)
        if form.is_valid():
            form.save()
            return redirect('listar_tareas')
    else:
        form = TareaForm(instance=tarea)

    return render(request, 'editar_tarea.html', {'form': form})

@login_required
def eliminar_tarea(request, pk):
    tarea = get_object_or_404(Tarea, pk=pk)
    if request.method == "POST":
        tarea.delete()
        return redirect('lista_tareas')

    return render(request, 'eliminar_tarea.html', {'tarea': tarea})



#Eventos
@login_required
def crear_evento(request):
    if request.method == 'POST':
        form = EventoForm(request.POST)
        if form.is_valid():

            perfil_usuario = PerfilUsuario.objects.get(usuario=request.user)
            evento = form.save(commit=False)
            evento.cofradia = perfil_usuario.cofradia  # Asignar la cofradía del usuario logueado
            evento.save()
            return redirect('lista_eventos')
    else:
        form = EventoForm()
    return render(request, 'crear_evento.html', {'form': form})

@login_required
def lista_eventos(request):
    # Obtener el parámetro de ordenación (por defecto será por 'id')
    order_by = request.GET.get('order_by', 'id')  # Si no se especifica, se ordena por 'id'
    valid_order_fields = ['id', 'nombre', 'fecha', 'tipo']
    
    # Si el 'order_by' no está en los campos válidos, usar 'id' como valor por defecto
    if order_by not in valid_order_fields:
        order_by = 'id'  # Orden por defecto en caso de un parámetro no válido
    
    # Filtros
    nombre_filter = request.GET.get('nombre', '')

    # Consultar todos los hermanos
    eventos = Evento.objects.all()

    # Aplicar filtros
    if nombre_filter:
        eventos = eventos.filter(Q(nombre__icontains=nombre_filter))

    # Ordenar según el 'order_by'
    eventos = eventos.order_by(order_by)

    return render(request, 'lista_eventos.html', {
        'eventos': eventos,
        'order_by': order_by,
        'nombre_filter': nombre_filter,
    })

login_required
def detalle_evento(request, pk):
    evento = get_object_or_404(Evento, pk=pk)
    return render(request, 'detalle_evento.html', {'evento': evento})

@login_required
def editar_evento(request, pk):
    evento = get_object_or_404(Evento, pk=pk)

    if request.method == "POST":
        form = EventoForm(request.POST, instance=evento)
        if form.is_valid():
            form.save()
            return redirect('listar_eventos')
    else:
        form = EventoForm(instance=evento)

    return render(request, 'editar_evento.html', {'form': form})

@login_required
def eliminar_evento(request, pk):
    evento = get_object_or_404(Evento, pk=pk)
    if request.method == "POST":
        evento.delete()
        return redirect('lista_eventos')

    return render(request, 'eliminar_evento.html', {'evento': evento})



#Configuracion
@login_required
def configuracion(request):
    return render(request, 'configuracion.html')

@login_required
def cargar_hermanos(request):
    if request.method == 'POST':
        form = CargarExcelForm(request.POST, request.FILES)
        
        if form.is_valid():
            archivo_excel = request.FILES['archivo_excel']

            try:
                df = pd.read_excel(archivo_excel, dtype={'TELEFONO': str})
                cofradia_usuario = request.user.perfilusuario.cofradia

                # Comenzamos la transacción atómica
                with transaction.atomic():  # Aquí empieza la transacción
                    for index, row in df.iterrows():
                        try:
                            # Obtener valores con `.get()` y manejar nulos
                            dni = str(row.get('DNI', '')).strip() or None
                            nombre = str(row.get('NOMBRE', '')).strip() or None
                            apellidos = str(row.get('APELLIDOS', '')).strip() or None
                            telefono = str(row.get('TELEFONO', '')).strip() or None
                            direccion = str(row.get('DIRECCION', '')).strip() or None
                            localidad = str(row.get('LOCALIDAD', '')).strip() or None
                            email = str(row.get('EMAIL', '')).strip() or None
                            iban = str(row.get('IBAN', '')).strip() or None

                            fecha_nacimiento = convertir_fecha(row.get('FECHA_NACIMIENTO'))
                            fecha_inicio = convertir_año(row.get('FECHA_INICIO'))
                            fecha_ultimo_pago = convertir_año(row.get('FECHA_ULTIMO_PAGO'))

                            estado, _ = Estado.objects.get_or_create(nombre=row.get('NOM_ESTADO', ''))
                            forma_pago, _ = FormaPago.objects.get_or_create(nombre=row.get('FORMA_PAGO', ''))
                            forma_comunicacion, _ = FormaComunicacion.objects.get_or_create(nombre=row.get('FORMA_COMUNICACION', ''))
                            cargo, _ = Cargo.objects.get_or_create(cargo='Hermano')

                            # Si el DNI existe, saltar fila
                            if dni and nombre and apellidos and Hermano.objects.filter(dni=dni, nombre=nombre, apellidos=apellidos).exists():
                                messages.info(request, f"La fila {index + 1} ya fue importada anteriormente (DNI: {dni}).")
                                continue

                            # Crear el hermano
                            hermano = Hermano.objects.create(
                                dni=dni,
                                nombre=nombre,
                                apellidos=apellidos,
                                telefono=telefono,
                                direccion=direccion,
                                localidad=localidad,
                                fecha_nacimiento=fecha_nacimiento,
                                fecha_inicio=fecha_inicio,
                                fecha_ultimo_pago=fecha_ultimo_pago,
                                estado=estado,
                                forma_pago=forma_pago,
                                forma_comunicacion=forma_comunicacion,
                                cofradia=cofradia_usuario,
                                email=email,
                                iban=iban,
                            )

                            # Crear usuario solo si hay DNI
                            if dni and not User.objects.filter(username=dni).exists():
                                user = User.objects.create_user(username=dni, password=dni, email=email)
                                PerfilUsuario.objects.create(usuario=user, cofradia=cofradia_usuario, cargo=cargo)
                                user.set_password(dni)  # Guardar contraseña de forma segura
                                user.save()

                        except Exception as e:
                            # Si algo falla, la transacción se deshace completamente
                            messages.error(request, f"Error en fila {index + 1}: {e}")
                            messages.error(request, f"Error con el dni {dni}")
                            messages.error(request, f"Error con el dni {telefono}")
                            messages.error(request, f"Error con el dni {estado}")
                            messages.error(request, f"Error con el dni {iban}")
                            raise  # Esto asegura que se interrumpa la ejecución de la transacción

                # Si todo fue bien, mostrar mensaje de éxito
                messages.success(request, 'Los hermanos han sido importados correctamente.')
                return redirect('configuracion/')

            except Exception as e:
                # Si hubo un error en el proceso general, revertir todo lo hecho dentro de la transacción
                messages.error(request, f'Error al procesar el archivo: {e}')
    
    else:
        form = CargarExcelForm()

    return render(request, 'cargar_hermanos.html', {'form': form})


def convertir_fecha(valor):
    try:
        return pd.to_datetime(valor).date() if pd.notna(valor) else None
    except:
        return None

def convertir_año(valor):
    try:
        return int(valor) if pd.notna(valor) else None
    except ValueError:
        return None
