from datetime import date, timedelta
from django.db import transaction
from django.db.models import Q, Sum
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.core.mail import send_mail
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.utils.timezone import now
from .forms import HermanoForm, EventoForm, TareaForm, EstadoForm, FormaPagoForm, FormaComunicacionForm, CofradiaForm, CargarExcelForm, InventarioForm, PrestamoForm, DonacionForm
from .models import PerfilUsuario, Cargo, Hermano, Estado, FormaPago, FormaComunicacion, Cofradia, Tarea, Evento, Finanza, AuditoriaHermano, Inventario, Prestamo, Donacion
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
import datetime, csv
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
    perfil_usuario = PerfilUsuario.objects.get(usuario=request.user)

    hermanos_total = Hermano.objects.filter(cofradia__nombre=perfil_usuario.cofradia).count()
    hermanos_activos = Hermano.objects.filter(cofradia__nombre=perfil_usuario.cofradia, estado=activo_estado).count()
    hermanos_no_pagados = Hermano.objects.filter(cofradia__nombre=perfil_usuario.cofradia, estado=no_pagado_estado).count()
    hermanos_baja = Hermano.objects.filter(cofradia__nombre=perfil_usuario.cofradia, estado=baja_estado).count()
    hermanos_fallecidos = Hermano.objects.filter(cofradia__nombre=perfil_usuario.cofradia, estado=fallecido_estado).count()

    pago_efectivo = Hermano.objects.filter(cofradia__nombre=perfil_usuario.cofradia, forma_pago=efectivo_pago).count()
    pago_transferencia = Hermano.objects.filter(cofradia__nombre=perfil_usuario.cofradia, forma_pago=transferencia_pago).count()
    pago_domiciliacion = Hermano.objects.filter(cofradia__nombre=perfil_usuario.cofradia, forma_pago=domiciliacion_pago).count()

    comunicacion_telefono = Hermano.objects.filter(cofradia__nombre=perfil_usuario.cofradia, forma_comunicacion=telefono_comunicacion).count()
    comunicacion_carta = Hermano.objects.filter(cofradia__nombre=perfil_usuario.cofradia, forma_comunicacion=carta_comunicacion).count()
    comunicacion_email = Hermano.objects.filter(cofradia__nombre=perfil_usuario.cofradia, forma_comunicacion=email_comunicacion).count()

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

            AuditoriaHermano.objects.create(
                hermano=hermano,
                accion="CREAR",
                usuario=request.user,
                detalles=f"Nuevo hermano registrado: {hermano.nombre} {hermano.apellidos}"
            )    

            return redirect('lista_hermanos')
    else:
        form = HermanoForm()
    return render(request, 'crear/crear_hermano.html', {'form': form})

@login_required
def lista_hermanos(request):
    order_by = request.GET.get('order_by', 'numero_hermano')
    valid_order_fields = ['numero_hermano', 'dni', 'nombre', 'apellidos', 'telefono', 'direccion', 'localidad', 'fecha_nacimiento', 'estado']
    
    if order_by not in valid_order_fields:
        order_by = 'numero_hermano'

    estado_filter = request.GET.get('estado', '')
    apellidos_filter = request.GET.get('apellidos', '')

    perfil_usuario = PerfilUsuario.objects.get(usuario=request.user)
    hermanos = Hermano.objects.filter(cofradia__nombre=perfil_usuario.cofradia)

    if estado_filter:
        hermanos = hermanos.filter(estado__nombre=estado_filter)
    if apellidos_filter:
        hermanos = hermanos.filter(Q(nombre__icontains=apellidos_filter) | Q(apellidos__icontains=apellidos_filter))

    hermanos = hermanos.order_by(order_by)

    # Paginación: 10 elementos por página
    paginator = Paginator(hermanos, 10)  # Cambia el número según lo necesites
    page = request.GET.get('page')

    try:
        hermanos = paginator.page(page)
    except PageNotAnInteger:
        hermanos = paginator.page(1)  # Si no es un número, mostrar la primera página
    except EmptyPage:
        hermanos = paginator.page(paginator.num_pages)  # Si está fuera de rango, mostrar la última

    return render(request, 'lista/lista_hermanos.html', {
        'hermanos': hermanos,
        'order_by': order_by,
        'estado_filter': estado_filter,
        'nombre_filter': apellidos_filter,
    })

login_required
def detalle_hermano(request, pk):
    hermano = get_object_or_404(Hermano, pk=pk)
    return render(request, 'detalle/detalle_hermano.html', {'hermano': hermano})

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

            AuditoriaHermano.objects.create(
                hermano=hermano,
                accion="MODIFICAR",
                usuario=request.user,
                detalles="Datos modificados"
            )

            return redirect('lista_hermanos')
    else:
        form = HermanoForm(instance=hermano)

    return render(request, 'editar/editar_hermano.html', {'form': form})

@login_required
def eliminar_hermano(request, pk):
    hermano = get_object_or_404(Hermano, pk=pk)
    if request.method == "POST":

        user = get_object_or_404(User, username=hermano.dni)
        perfilUsuario = get_object_or_404(PerfilUsuario, usuario=user)

        perfilUsuario.delete()
        user.delete()
        hermano.delete()

        AuditoriaHermano.objects.create(
            hermano=hermano,
            accion="ELIMINAR",
            usuario=request.user,
            detalles="Hermano eliminado del sistema"
        )

        messages.success(request, f'El hermano "{hermano.nombre}"  "{hermano.apellidos}" ha sido eliminado con éxito.')

        return redirect('listar_hermanos')

    return redirect('listar_hermanos')



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
    return render(request, 'crear/crear_tarea.html', {'form': form})

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

    return render(request, 'lista/lista_tareas.html', {
        'tareas': tareas,
        'order_by': order_by,
        'titulo_filter': titulo_filter,
        'estado_filter': estado_filter,
        'prioridad_filter': prioridad_filter,
    })

login_required
def detalle_tarea(request, pk):
    tarea = get_object_or_404(Tarea, pk=pk)
    return render(request, 'detalle/detalle_tarea.html', {'tarea': tarea})

@login_required
def editar_tarea(request, pk):
    tarea = get_object_or_404(Tarea, pk=pk)

    if request.method == "POST":
        form = TareaForm(request.POST, instance=tarea)
        if form.is_valid():
            form.save()
            return redirect('lista_tareas')
    else:
        form = TareaForm(instance=tarea)

    return render(request, 'editar/editar_tarea.html', {'form': form})

@login_required
def eliminar_tarea(request, pk):
    # Obtener la tarea a eliminar
    tarea = get_object_or_404(Tarea, id=pk)
    
    # Verificar que la solicitud sea un POST (para evitar eliminar accidentalmente con GET)
    if request.method == 'POST':
        tarea.delete()  # Eliminar la tarea

        # Mostrar un mensaje de éxito
        messages.success(request, f'La tarea "{tarea.titulo}" ha sido eliminada con éxito.')

        # Redirigir al usuario de vuelta a la lista de tareas
        return redirect('lista_tareas')  # Asegúrate de que 'lista_tareas' es el nombre correcto de la vista

    # Si la solicitud no es un POST, redirigir al usuario de vuelta (aunque no debería llegar aquí por el tipo de formulario)
    return redirect('lista_tareas')



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
    return render(request, 'crear/crear_evento.html', {'form': form})

@login_required
def lista_eventos(request):
    # Obtener el parámetro de ordenación (por defecto será por 'id')
    order_by = request.GET.get('order_by', 'fecha')  # Si no se especifica, se ordena por 'id'
    order_direction = request.GET.get('order_direction', 'desc')  # 'asc' o 'desc'
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
    if order_direction == 'desc':
        eventos = eventos.order_by(f'-{order_by}')
    else:
        eventos = eventos.order_by(order_by)

    return render(request, 'lista/lista_eventos.html', {
        'eventos': eventos,
        'order_by': order_by,
        'nombre_filter': nombre_filter,
    })

login_required
def detalle_evento(request, pk):
    evento = get_object_or_404(Evento, pk=pk)
    return render(request, 'detalle/detalle_evento.html', {'evento': evento})

@login_required
def editar_evento(request, pk):
    evento = get_object_or_404(Evento, pk=pk)

    if request.method == "POST":
        form = EventoForm(request.POST, instance=evento)
        if form.is_valid():
            form.save()
            return redirect('lista_eventos')
    else:
        form = EventoForm(instance=evento)

    return render(request, 'editar/editar_evento.html', {'form': form})

@login_required
def eliminar_evento(request, pk):
    # Obtener el evento a eliminar
    evento = get_object_or_404(Evento, id=pk)
    
    # Verificar que la solicitud sea un POST (para evitar eliminar accidentalmente con GET)
    if request.method == 'POST':
        evento.delete()  # Eliminar el evento

        # Mostrar un mensaje de éxito
        messages.success(request, f'El evento "{evento.nombre}" ha sido eliminado con éxito.')

        # Redirigir al usuario de vuelta a la lista de eventos
        return redirect('lista_eventos')  # Asegúrate de que 'lista_eventos' es el nombre correcto de la vista

    # Si la solicitud no es un POST, redirigir al usuario de vuelta (aunque no debería llegar aquí por el tipo de formulario)
    return redirect('lista_eventos')



#Inventario
@login_required
def crear_inventario(request):
    if request.method == 'POST':
        form = InventarioForm(request.POST)
        if form.is_valid():
            inventario = form.save(commit=False)
            inventario.cofradia = request.user.perfilusuario.cofradia
            inventario.save()
            return redirect('lista_inventario')
    else:
        form = InventarioForm()

    return render(request, 'crear/crear_inventario.html', {'form': form})

@login_required
def lista_inventario(request):
    # Obtener el parámetro de ordenación (por defecto será por 'id')
    order_by = request.GET.get('order_by', 'id')  # Si no se especifica, se ordena por 'id'
    valid_order_fields = ['id', 'nombre', 'descripcion', 'cantidad_disponible', 'ubicacion']
    
    # Si el 'order_by' no está en los campos válidos, usar 'id' como valor por defecto
    if order_by not in valid_order_fields:
        order_by = 'id'  # Orden por defecto en caso de un parámetro no válido
    
    # Filtros
    nombre_filter = request.GET.get('nombre', '')

    # Consultar todos los hermanos
    inventarios = Inventario.objects.all()

    # Aplicar filtros
    if nombre_filter:
        inventarios = inventarios.filter(Q(nombre__icontains=nombre_filter))

    # Ordenar según el 'order_by'
    inventarios = inventarios.order_by(order_by)

    return render(request, 'lista/lista_inventario.html', {
        'inventarios': inventarios,
        'order_by': order_by,
        'nombre_filter': nombre_filter,
    })

@login_required
def detalle_inventario(request, pk):
    inventario = get_object_or_404(Inventario, pk=pk)
    return render(request, 'detalle/detalle_inventario.html', {'inventario': inventario})

@login_required
def editar_inventario(request, pk):
    inventario = get_object_or_404(Inventario, pk=pk)

    if request.method == "POST":
        form = InventarioForm(request.POST, instance=inventario)
        if form.is_valid():
            form.save()
            return redirect('lista_inventario')
    else:
        form = InventarioForm(instance=inventario)

    return render(request, 'editar/editar_inventario.html', {'form': form})

@login_required
def eliminar_inventario(request, pk):
    inventario = get_object_or_404(Inventario, pk=pk)
    if request.method == "POST":
        inventario.delete()

        # Mostrar un mensaje de éxito
        messages.success(request, f'El inventario "{inventario.nombre}" ha sido eliminado con éxito.')

        return redirect('lista_inventario')
    
    return redirect('lista_inventario')



#Prestamos
@login_required
def crear_prestamo(request):
    if request.method == 'POST':
        form = PrestamoForm(request.POST)
        if form.is_valid():
            prestamo = form.save(commit=False)
            # Definir la fecha de préstamo
            prestamo.fecha_prestamo = request.POST.get('fecha_prestamo', None) or None
            prestamo.save()
            # Reducir la cantidad disponible del material prestado
            inventario = prestamo.inventario
            inventario.cantidad_disponible -= 1
            inventario.save()
            messages.success(request, 'Préstamo registrado correctamente.')
            return redirect('lista_prestamos')
    else:
        form = PrestamoForm()

    return render(request, 'crear/crear_prestamo.html', {'form': form})

@login_required
def lista_prestamos(request):
    query = request.GET.get('hermano', '')  # Obtiene el parámetro 'usuario' de la URL
    prestamos = Prestamo.objects.all()

    if query:
        prestamos = prestamos.filter(hermano__nombre__icontains=query)  # Filtra por nombre de usuario

    return render(request, 'lista/lista_prestamos.html', {'prestamos': prestamos, 'hermano_filter': query})

@login_required
def detalle_prestamo(request, pk):
    prestamo = get_object_or_404(Prestamo, pk=pk)
    return render(request, 'detalle/detalle_prestamo.html', {'prestamo': prestamo})

@login_required
def editar_prestamo(request, pk):
    prestamo = get_object_or_404(Prestamo, pk=pk)

    if request.method == "POST":
        form = PrestamoForm(request.POST, instance=prestamo)
        if form.is_valid():
            form.save()
            messages.success(request, 'Préstamo actualizado correctamente.')
            return redirect('lista_prestamos')
    else:
        form = PrestamoForm(instance=prestamo)

    return render(request, 'editar/editar_prestamo.html', {'form': form})

@login_required
def eliminar_prestamo(request, pk):
    prestamo = get_object_or_404(Prestamo, pk=pk)
    if request.method == "POST":
        inventario = prestamo.inventario
        # Devolver el material (aumentar la cantidad disponible)
        inventario.cantidad_disponible += 1
        inventario.save()
        prestamo.delete()
        messages.success(request, f'El prestamo de "{prestamo.inventario.nombre}" al hermano "{prestamo.hermano.nombre}" "{prestamo.hermano.apellidos}" ha sido eliminado con éxito.')
        return redirect('lista_prestamos')

    return redirect('lista_prestamos')



#Informes
def generar_pdf(nombre_archivo, encabezados, datos):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename={nombre_archivo}.pdf'

    # Configurar el PDF en apaisado
    doc = SimpleDocTemplate(response, pagesize=landscape(letter))
    elements = []

    # Crear la tabla con encabezados + datos
    tabla_datos = [encabezados] + datos

    # Ajuste automático de columnas (misma anchura para todas)
    num_columnas = len(encabezados)
    column_widths = [landscape(letter)[0] / num_columnas] * num_columnas  

    table = Table(tabla_datos, colWidths=column_widths)

    # Aplicar estilos a la tabla
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),  # Fondo gris en encabezados
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),  # Texto blanco en encabezados
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  # Centrar texto
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Negrita en encabezados
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),  # Espaciado en encabezados
        ('GRID', (0, 0), (-1, -1), 1, colors.black),  # Bordes negros
    ]))

    elements.append(table)
    doc.build(elements)

    return response

@login_required
def informes_view(request):
    informes = [
        {"titulo": "Hermanos (Ordenado por Apellido)", "descripcion": "Descarga un listado ordenado alfabéticamente.", "url": "informe_hermanos_alfabetico"},
        {"titulo": "Hermanos Mayores de Edad", "descripcion": "Consulta los miembros mayores de edad.", "url": "informe_mayores_edad"},
        {"titulo": "Cuotas Pendientes", "descripcion": "Lista de hermanos con pagos pendientes.", "url": "informe_cuotas_pendientes"},
        {"titulo": "Antigüedad de Hermanos", "descripcion": "Ordenado por años de pertenencia.", "url": "informe_antiguedad"},
        {"titulo": "Eventos del Año", "descripcion": "Resumen de actividades y reuniones.", "url": "informe_eventos"},
        {"titulo": "Resumen Financiero", "descripcion": "Informe de ingresos y gastos.", "url": "informe_finanzas"},
        {"titulo": "Tareas Pendientes", "descripcion": "Listado de tareas aún sin completar.", "url": "informe_tareas_pendientes"},
    ]
    return render(request, 'informes.html', {"informes": informes})

@login_required
def informe_hermanos_alfabetico(request):
    hermanos = Hermano.objects.all().order_by('apellidos')
    datos = [(h.dni, h.nombre, h.apellidos, h.telefono, h.direccion, h.fecha_nacimiento, h.email, h.estado, h.forma_comunicacion, h.forma_pago) for h in hermanos]

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="Hermanos.pdf"'

    doc = SimpleDocTemplate(response, pagesize=landscape(letter))
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph("Informe de Hermanos Ordenados por Apellido", styles['Title']))
    elements.append(Spacer(1, 12))

    col_widths = [50, 100, 120, 52, 140, 50, 100, 50, 50, 50]
    encabezados = ["DNI", "Nombre", "Apellidos", "Teléfono", "Dirección", "Fecha nacimiento", "Email", "Estado", "Forma Comunicacion", "Forma Pago"]
    
    # Crear un Paragraph para cada celda del encabezado para permitir el salto de línea
    encabezados_paragraph = [
        Paragraph(f'<b>{header}</b>', 
                  ParagraphStyle('HeaderStyle', fontSize=10, textColor=colors.white, alignment=1)) 
        for header in encabezados
    ]

    tabla_datos = [encabezados_paragraph] + datos
    table = Table(tabla_datos, colWidths=col_widths)

    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
        ('WORDWRAP', (0, 0), (-1, -1), True)  # Habilitar el salto de línea en las celdas
    ]))

    normal_style = ParagraphStyle('NormalStyle', parent=styles['Normal'], fontSize=8)

    elements.append(table)
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"Generado el {date.today().strftime('%d/%m/%Y')}", normal_style))

    doc.build(elements)
    return response

@login_required
def informe_mayores_edad(request):
    # Datos
    hoy = date.today()
    hermanos = Hermano.objects.filter(fecha_nacimiento__lte=hoy.replace(year=hoy.year - 18)).order_by('apellidos')
    datos = [(h.dni, h.nombre, h.apellidos, h.telefono, h.fecha_nacimiento.strftime("%d-%m-%Y")) for h in hermanos]

    # Respuesta HTTP para PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="hermanos_mayores.pdf"'

    # Crear documento
    doc = SimpleDocTemplate(response, pagesize=landscape(letter))
    elements = []
    styles = getSampleStyleSheet()

    # **Encabezado**
    elements.append(Paragraph("Informe de Hermanos Mayores de Edad", styles['Title']))
    elements.append(Spacer(1, 12))

    # **Tabla de Datos**
    encabezados = ["DNI", "Nombre", "Apellidos", "Telefono", "Fecha de Nacimiento"]
    tabla_datos = [encabezados] + datos

    # Ajuste automático de columnas
    col_widths = [65, 150, 150, 65, 105]
    
    table = Table(tabla_datos, colWidths=col_widths)

    # **Estilos de la tabla**
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey])
    ]))

    elements.append(table)
    elements.append(Spacer(1, 12))

    # **Pie de Página con Fecha**
    elements.append(Paragraph(f"Generado el {hoy.strftime('%d/%m/%Y')}", styles['Normal']))

    doc.build(elements)

    return response

@login_required
def informe_cuotas_pendientes(request):
    hermanos = Hermano.objects.filter(cuota_pendiente__gt=0).order_by('apellidos')
    datos = [(h.dni, h.nombre, h.apellidos, f"{h.cuota_pendiente} €") for h in hermanos]

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="Cuotas_Pendientes.pdf"'

    doc = SimpleDocTemplate(response, pagesize=landscape(letter))
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph("Informe de Cuotas Pendientes", styles['Title']))
    elements.append(Spacer(1, 12))

    col_widths = [80, 150, 150, 120]
    encabezados = ["DNI", "Nombre", "Apellidos", "Cuota Pendiente"]
    tabla_datos = [encabezados] + datos
    table = Table(tabla_datos, colWidths=col_widths)

    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkred),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey])
    ]))

    elements.append(table)
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"Generado el {date.today().strftime('%d/%m/%Y')}", styles['Normal']))

    doc.build(elements)
    return response

@login_required
def informe_antiguedad(request):
    hermanos = Hermano.objects.all().order_by('fecha_inicio')
    datos = [(h.dni, h.nombre, h.apellidos, h.fecha_inicio) for h in hermanos]
    return generar_pdf('Hermanos_por_Antiguedad.pdf', ['DNI', 'Nombre', 'Apellidos', 'Año de Inicio'], datos)

@login_required
def informe_eventos(request):
    eventos = Evento.objects.filter(fecha__year=date.today().year).order_by('fecha')
    datos = [(e.nombre, e.fecha, e.tipo) for e in eventos]
    return generar_pdf('Eventos_Anuales.pdf', ['Nombre', 'Fecha', 'Tipo'], datos)

@login_required
def informe_finanzas(request):
    finanzas = Finanza.objects.all().order_by('fecha')
    datos = [(f.tipo, f.monto, f.fecha) for f in finanzas]
    return generar_pdf('Resumen_Finanzas.pdf', ['Tipo', 'Monto', 'Fecha'], datos)

@login_required
def informe_tareas_pendientes(request):
    tareas = Tarea.objects.filter(estado__in=['Pendiente', 'Atrasada'])
    datos = [(t.titulo, t.asignado_a, t.fecha_limite, t.estado, t.prioridad) for t in tareas]
    return generar_pdf('Tareas_Pendientes.pdf', ['Título', 'Asignado A', 'Fecha Límite', 'Estado', 'Prioridad'], datos)



@login_required
def crear_donacion(request):
    if request.method == 'POST':
        form = DonacionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Donación registrada correctamente.")
            return redirect('lista_donaciones')  # Redirige a la lista de donaciones
        else:
            messages.error(request, "Error al registrar la donación. Por favor, revisa los campos.")
    else:
        form = DonacionForm()

    return render(request, 'crear/crear_donacion.html', {'form': form})

@login_required
def lista_donaciones(request):
    donaciones = Donacion.objects.all()
    return render(request, 'lista/lista_donaciones.html', {'donaciones': donaciones})



#Notificaciones
def enviar_correo(request):
    hermanos_con_email = Hermano.objects.filter(email__isnull=False).exclude(email="")  # Solo hermanos con email

    if request.method == 'POST':
        asunto = request.POST.get('asunto')
        mensaje = request.POST.get('mensaje')
        destinatario_id = request.POST.get('destinatario')  # Puede ser 'todos' o un ID

        if asunto and mensaje:
            if destinatario_id == "todos":
                destinatarios = list(hermanos_con_email.values_list('email', flat=True))
            else:
                hermano = hermanos_con_email.filter(id=destinatario_id).first()
                destinatarios = [hermano.email] if hermano else []

            if destinatarios:
                try:
                    send_mail(
                        asunto,
                        mensaje,
                        settings.EMAIL_HOST_USER,
                        destinatarios,
                        fail_silently=False,
                    )
                    messages.success(request, f"Correo enviado a {len(destinatarios)} destinatario(s).")
                except Exception as e:
                    messages.error(request, f"Error al enviar el correo: {e}")
            else:
                messages.warning(request, "No hay destinatarios válidos.")

        else:
            messages.warning(request, "Por favor, completa todos los campos.")

        return redirect('enviar_correo')

    return render(request, 'enviar_correo.html', {'hermanos': hermanos_con_email})



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
