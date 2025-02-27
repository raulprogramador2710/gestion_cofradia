# gestion_cofradia/views.py
from django import forms
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User, Group
from django.contrib.auth.views import PasswordChangeView
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy

from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from datetime import date, timedelta

from .forms import HermanoForm
from .models import Hermano, PerfilUsuario, Cofradia


def custom_login(request):
     # Obtener el color de la base de datos
    cofradia = Cofradia.objects.first()  # Ajusta si hay varias cofradías
    color_principal = cofradia.color if cofradia else "#000000"  # Color por defecto

    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('inicio')  # Redirigir tras el login

    return render(request, "gestion_cofradia/login.html", {"color_principal": color_principal})

@login_required
def inicio(request):
    return render(request, 'gestion_cofradia/inicio.html')

@login_required
@permission_required('gestion_cofradia.puede_ver_hermanos', raise_exception=True)
def listar_hermanos(request):
    usuario = request.user

    if usuario.is_superuser:
        # El admin puede ver todos los hermanos
        hermanos = Hermano.objects.all()
    elif hasattr(usuario, "perfilusuario"):
        perfil = usuario.perfilusuario
        
        if perfil.es_secretario:
            # Si el usuario es secretario, solo ve los hermanos de su cofradía
            hermanos = Hermano.objects.filter(cofradia=perfil.cofradia)
        else:
            # Si el usuario no es secretario, solo ve su propio perfil de hermano
            hermanos = Hermano.objects.filter(perfil_usuario=perfil)
    else:
        hermanos = Hermano.objects.none()  # Si no tiene perfil, no puede ver hermanos

    return render(request, "gestion_cofradia/lista_hermanos.html", {"hermanos": hermanos})

@login_required
def descargar_informes(request):
    # Lógica para permitir la descarga de informes
    return render(request, 'descargar_informes.html')

@login_required
def gestion_economica(request):
    # Lógica para la futura gestión económica
    return render(request, 'gestion_economica.html')

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

class CustomPasswordChangeView(PasswordChangeView):
    template_name = 'gestion_cofradia/password_change.html'
    success_url = reverse_lazy('listar_hermanos')

    def form_valid(self, form):
        response = super().form_valid(form)
        # Marcar que el usuario ya cambió la contraseña
        user_profile = UserProfile.objects.get(user=self.request.user)
        user_profile.password_reset_required = False
        user_profile.save()
        return response

@login_required
@permission_required('auth.add_user', raise_exception=True)  # Solo administradores y secretarios
def registrar_usuario(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            group = Group.objects.get(name='Secretario')  # O asignar grupo adecuado
            user.groups.add(group)
            return redirect('listar_hermanos')  # Redirigir a la lista de hermanos
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'gestion_cofradia/registrar_usuario.html', {'form': form})        

@login_required
@permission_required('gestion_cofradia.puede_ver_hermanos', raise_exception=True)
def detalle_hermano(request, pk):
    hermano = get_object_or_404(Hermano, pk=pk)
    return render(request, 'gestion_cofradia/detalle_hermano.html', {'hermano': hermano})

@login_required
@permission_required('gestion_cofradia.puede_crear_hermanos', raise_exception=True)
def crear_hermano(request):
    # Comprobamos el tipo de usuario para determinar el comportamiento
    if request.user.is_superuser:
        # Si el usuario es admin, puede elegir cualquier cofradía
        cofradias = Cofradia.objects.all()
    elif request.user.perfilusuario.es_secretario:
        # Si el usuario es secretario, asignamos automáticamente su cofradía al nuevo hermano
        cofradias = Cofradia.objects.filter(pk=request.user.perfilusuario.cofradia.pk)  # Pasamos un QuerySet
    else:
        # Si es un hermano normal, no podrá crear un nuevo hermano
        return redirect('listar_hermanos')  # Redirigimos a la lista de hermanos (no puede crear)

    if request.method == 'POST':
        form = HermanoForm(request.POST)
        if form.is_valid():
            hermano = form.save(commit=False)

            if request.user.is_superuser:
                # Si es un admin, asigna la cofradía seleccionada
                cofradia_seleccionada = form.cleaned_data['cofradia']
                hermano.cofradia = cofradia_seleccionada
            elif request.user.perfilusuario.es_secretario:
                # Si es secretario, asignamos automáticamente su cofradía
                hermano.cofradia = request.user.perfilusuario.cofradia

            # 1️⃣ CREAR UN NUEVO USUARIO PARA EL HERMANO
            nuevo_usuario = User.objects.create_user(
                username=form.cleaned_data['dni'],  # Puedes cambiar esto según el formulario
                password=form.cleaned_data['dni'],  # Se recomienda generar o pedir una contraseña
                first_name=form.cleaned_data['nombre'],
                last_name=form.cleaned_data['apellidos'],
                email=form.cleaned_data['email']
            )

            # 2️⃣Asignar el usuario a un grupo (si lo necesitas)
            grupo_hermanos = Group.objects.get(name="Usuario")  # Asegúrate de que el grupo existe
            nuevo_usuario.groups.add(grupo_hermanos)

            # 2️⃣ CREAR EL PERFIL PARA EL NUEVO USUARIO
            nuevo_perfil = PerfilUsuario.objects.create(
                usuario=nuevo_usuario,
                cofradia=hermano.cofradia
            )

            # 3️⃣ ASOCIAR EL NUEVO PERFIL AL HERMANO
            hermano.perfil_usuario = nuevo_perfil
            hermano.save()

            return redirect('listar_hermanos')  # Redirige a la lista de hermanos
    else:
        # Si el usuario es admin, le mostramos todas las cofradías
        if request.user.is_superuser:
            form = HermanoForm()
        # Si es secretario, solo le mostramos su cofradía
        elif request.user.perfilusuario.es_secretario:
            form = HermanoForm(cofradias=Cofradia.objects.filter(pk=request.user.perfilusuario.cofradia.pk))

    return render(request, 'gestion_cofradia/crear_hermano.html', {'form': form})

@login_required
@permission_required('gestion_cofradia.puede_editar_hermanos', raise_exception=True)
def editar_hermano(request, pk):
    hermano = get_object_or_404(Hermano, pk=pk)

    if request.method == "POST":
        form = HermanoForm(request.POST, instance=hermano)

        # Guardar los datos si el formulario es válido
        if form.is_valid():
            form.save()
            return redirect('listar_hermanos')  # Redirige a la lista de hermanos después de guardar
    else:
        form = HermanoForm(instance=hermano)

    return render(request, 'gestion_cofradia/editar_hermano.html', {'form': form})

@login_required
@permission_required('gestion_cofradia.puede_eliminar_hermanos', raise_exception=True)
def eliminar_hermano(request, pk):
    hermano = get_object_or_404(Hermano, pk=pk)
    if request.method == "POST":
        hermano.delete()
        return redirect('listar_hermanos')

    return render(request, 'gestion_cofradia/eliminar_hermano.html', {'hermano': hermano})

def logout_view(request):
    logout(request)  # Cierra la sesión
    return redirect('login')  # Redirige al login o a otra página después del logout






@login_required
@permission_required('gestion_cofradia.puede_ver_hermanos', raise_exception=True)
def informes(request):
    return render(request, 'gestion_cofradia/informes.html')

@login_required
@permission_required('gestion_cofradia.puede_ver_hermanos', raise_exception=True)
def descargar_hermanos_pdf(request):
    # Crear la respuesta HTTP con el tipo de contenido adecuado
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="hermanos.pdf"'

    # Configurar el documento en formato apaisado
    doc = SimpleDocTemplate(response, pagesize=landscape(letter))
    elements = []

    # Obtener todos los hermanos de la base de datos
    hermanos = Hermano.objects.all().order_by('apellidos')

    # Crear la cabecera de la tabla
    data = [["DNI", "Nombre", "Apellidos", "Teléfono", "Dirección", "Localidad", "Fecha Nac.", "Email", "Estado", "Forma Pago"]]

    # Agregar los datos de cada hermano
    for hermano in hermanos:
        data.append([
            hermano.dni, hermano.nombre, hermano.apellidos, hermano.telefono,
            hermano.direccion, hermano.localidad, hermano.fecha_nacimiento.strftime("%d/%m/%Y"),
            hermano.email if hermano.email else "N/A", hermano.estado, hermano.forma_pago
        ])

    # Ajuste individual de columnas (en puntos, 1 punto ≈ 0.35mm)
    col_widths = [
        45,   # DNI (máx. 9 caracteres)
        60,   # Nombre
        90,   # Apellidos
        45,   # Teléfono (máx. 9 caracteres)
        180,  # Dirección (más ancha por posibles textos largos)
        90,   # Localidad
        45,   # Fecha de Nacimiento
        130,  # Email (puede ser largo)
        35,   # estado
        40   # Forma Pago
    ]

    # Crear la tabla
    table = Table(data, colWidths=col_widths)

    # Estilizar la tabla
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.gray),  # Fondo gris en la cabecera
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),  # Texto blanco en cabecera
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  # Centrar el texto
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Fuente en negrita para cabecera
        ('FONTSIZE', (0, 0), (-1, -1), 8),  # Tamaño de fuente
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),  # Espaciado en cabecera
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),  # Fondo de filas
        ('GRID', (0, 0), (-1, -1), 1, colors.black)  # Bordes en la tabla
    ])
    table.setStyle(style)

    # Agregar la tabla al PDF
    elements.append(table)

    # Construir el documento
    doc.build(elements)
    return response

def descargar_hermanos_mayores_pdf(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="hermanos_mayores.pdf"'

    # Configurar el documento en formato apaisado
    doc = SimpleDocTemplate(response, pagesize=landscape(letter))
    elements = []

    # Calcular la fecha límite para ser mayor de edad
    fecha_limite = date.today().replace(year=date.today().year - 18)

    # Filtrar hermanos que sean mayores de edad y ordenarlos por apellidos
    hermanos = Hermano.objects.filter(fecha_nacimiento__lte=fecha_limite).order_by('apellidos')

    # Crear la cabecera de la tabla
    data = [["DNI", "Nombre", "Apellidos", "Teléfono", "Dirección", "Localidad", "Fecha Nac.", "Email", "Estado", "Forma Pago"]]

    # Agregar los datos de cada hermano
    for hermano in hermanos:
        data.append([
            hermano.dni, hermano.nombre, hermano.apellidos, hermano.telefono,
            hermano.direccion, hermano.localidad, hermano.fecha_nacimiento.strftime("%d/%m/%Y"),
            hermano.email if hermano.email else "N/A", hermano.estado, hermano.forma_pago
        ])

    # Ajuste individual de columnas (en puntos)
    col_widths = [45, 60, 90, 45, 180, 90, 45, 130, 35, 40]

    # Crear la tabla
    table = Table(data, colWidths=col_widths)

    # Estilizar la tabla
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.gray),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ])
    table.setStyle(style)

    # Agregar la tabla al PDF
    elements.append(table)

    # Construir el documento
    doc.build(elements)
    return response
