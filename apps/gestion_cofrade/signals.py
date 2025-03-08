# cofradia/signals.py
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Max
from django.db.models.signals import pre_save
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .models import Cofradia, Cargo, PerfilUsuario, Estado, FormaPago, FormaComunicacion, Hermano, Evento, Tarea, Inventario, Prestamo, Donacion

# Signal para asignar el número de hermano autoincremental dentro de cada cofradía
@receiver(pre_save, sender=Hermano)
def set_numero_hermano(sender, instance, **kwargs):
    if instance.numero_hermano is None:  # Si el número no ha sido asignado aún
        # Obtener el número máximo de hermano actual en la misma cofradía
        max_numero = Hermano.objects.filter(cofradia=instance.cofradia).aggregate(Max('numero_hermano'))['numero_hermano__max']
        if max_numero is None:
            instance.numero_hermano = 1  # Si no hay hermanos, empieza con el número 1
        else:
            instance.numero_hermano = max_numero + 1  # Incrementa el número más alto para esta cofradía

# Signal para asignar el identificador autoincremental dentro de cada cofradía
@receiver(pre_save, sender=Donacion)
@receiver(pre_save, sender=Prestamo)
def set_identificador(sender, instance, **kwargs):
    if instance.identificador is None:  # Si el identificador no ha sido asignado aún
        # Obtener el número máximo de identificador actual para la misma cofradía
        max_identificador = sender.objects.filter(cofradia=instance.cofradia).aggregate(Max('identificador'))['identificador__max']
        
        if max_identificador is None:
            instance.identificador = 1  # Si no hay registros previos, empieza con el número 1
        else:
            instance.identificador = max_identificador + 1  # Incrementa el número más alto para esta cofradía

# Función para crear los datos de prueba
@receiver(post_migrate)
def crear_datos_prueba(sender, **kwargs):
    # Borrar todos los datos de la Cofradía DEMO y sus dependencias
    cofradia_demo = Cofradia.objects.filter(nombre="Cofradía DEMO").first()
    if cofradia_demo:
        # Eliminar los datos relacionados con esta cofradía
        Prestamo.objects.filter(hermano__cofradia=cofradia_demo).delete()
        Inventario.objects.filter(cofradia=cofradia_demo).delete()
        Tarea.objects.filter(cofradia=cofradia_demo).delete()
        Evento.objects.filter(cofradia=cofradia_demo).delete()

        PerfilUsuario.objects.filter(cofradia=cofradia_demo).delete()

        dnis_a_eliminar = Hermano.objects.filter(cofradia__nombre="Cofradía DEMO").values_list('dni', flat=True)
        # Eliminar los usuarios cuyo username coincida con esos DNIs
        User.objects.filter(username__in=dnis_a_eliminar).delete()

        Hermano.objects.filter(cofradia=cofradia_demo).delete()

        PerfilUsuario.objects.filter(cofradia=cofradia_demo).delete()
        User.objects.filter(username='HM_Demo').delete()

        cofradia_demo.delete()

    # Crear una nueva Cofradía DEMO
    cofradia_demo = Cofradia.objects.create(
        nombre="Cofradía DEMO",
        descripcion="Esta es una Cofradía de ejemplo para pruebas.",
        color="#ff5733"  # Color HEX de ejemplo
    )
  
    user_demo = User.objects.create_user(username='HM_Demo', password='Demo1234')
    PerfilUsuario.objects.create(usuario=user_demo, cofradia=cofradia_demo, cargo=Cargo.objects.get(cargo='Hermano Mayor'))


    # Crear algunos Hermanos
    estado_activo = Estado.objects.get(nombre="Activo")
    estado_no_pagado = Estado.objects.get(nombre="No Pagado")
    estado_baja = Estado.objects.get(nombre="Baja")
    estado_fallecido = Estado.objects.get(nombre="Fallecido")
    
    forma_pago_efectivo = FormaPago.objects.get(nombre="Efectivo")
    forma_pago_transferencia = FormaPago.objects.get(nombre="Transferencia")
    forma_pago_domiciliación = FormaPago.objects.get(nombre="Domiciliación")

    forma_comunicacion_whatsapp = FormaComunicacion.objects.get(nombre="Whatsapp")
    forma_comunicacion_carta = FormaComunicacion.objects.get(nombre="Carta Postal")
    forma_comunicacion_email = FormaComunicacion.objects.get(nombre="Email")

    hermano1 = Hermano.objects.create(
        numero_hermano = "1",
        dni="12345678A",
        nombre="Juan",
        apellidos="Pérez García",
        telefono="600123456",
        direccion="Calle Falsa 123",
        localidad="Madrid",
        fecha_nacimiento="1990-01-01",
        fecha_inicio=2010,
        fecha_ultimo_pago=2025,
        email="juan@example.com",
        iban="ES7921000813610123456789",
        estado=estado_activo,
        forma_pago=forma_pago_efectivo,
        forma_comunicacion=forma_comunicacion_whatsapp,
        cofradia=cofradia_demo
    )

    hermano2 = Hermano.objects.create(
        numero_hermano = "2",
        dni="23456789B",
        nombre="Ana",
        apellidos="Lopez Pérez",
        telefono="600654321",
        direccion="Calle Falsa 456",
        localidad="Barcelona",
        fecha_nacimiento="1985-05-10",
        fecha_inicio=2015,
        fecha_ultimo_pago=2025,
        email="ana@example.com",
        iban="ES7921000813610123456789",
        estado=estado_no_pagado,
        forma_pago=forma_pago_transferencia,
        forma_comunicacion=forma_comunicacion_carta,
        cofradia=cofradia_demo
    )

    hermano3 = Hermano.objects.create(
        numero_hermano = "3",
        dni="34567890C",
        nombre="Carlos",
        apellidos="Martínez Gómez",
        telefono="600987654",
        direccion="Calle Ejemplo 789",
        localidad="Sevilla",
        fecha_nacimiento="1995-03-25",
        fecha_inicio=2018,
        fecha_ultimo_pago=2025,
        email="carlos@example.com",
        iban="ES7921000813610123456789",
        estado=estado_baja,
        forma_pago=forma_pago_domiciliación,
        forma_comunicacion=forma_comunicacion_email,
        cofradia=cofradia_demo
    )

    hermano4 = Hermano.objects.create(
        numero_hermano = "4",
        dni="45678901D",
        nombre="Lucía",
        apellidos="Fernández López",
        telefono="600345678",
        direccion="Calle Ejemplo 1011",
        localidad="Valencia",
        fecha_nacimiento="1992-07-14",
        fecha_inicio=2012,
        fecha_ultimo_pago=2024,
        email="lucia@example.com",
        iban="ES7921000813610123456789",
        estado=estado_fallecido,
        forma_pago=forma_pago_efectivo,
        forma_comunicacion=forma_comunicacion_whatsapp,
        cofradia=cofradia_demo
    )

    #Crear user y perfil usuario
    user_1= User.objects.create_user(username=hermano1.dni, password=hermano1.dni)
    PerfilUsuario.objects.create(usuario=user_1, cofradia=cofradia_demo, cargo=Cargo.objects.get(cargo='Hermano'))

    user_2 = User.objects.create_user(username=hermano2.dni, password=hermano2.dni)
    PerfilUsuario.objects.create(usuario=user_2, cofradia=cofradia_demo, cargo=Cargo.objects.get(cargo='Hermano'))

    user_3 = User.objects.create_user(username=hermano3.dni, password=hermano3.dni)
    PerfilUsuario.objects.create(usuario=user_3, cofradia=cofradia_demo, cargo=Cargo.objects.get(cargo='Hermano'))

    user_4 = User.objects.create_user(username=hermano4.dni, password=hermano4.dni)
    PerfilUsuario.objects.create(usuario=user_4, cofradia=cofradia_demo, cargo=Cargo.objects.get(cargo='Hermano'))

    # Crear Eventos de ejemplo
    evento1 = Evento.objects.create(
        nombre="Procesión Semana Santa",
        fecha="2025-04-13",
        tipo="Procesión",
        cofradia=cofradia_demo
    )

    evento2 = Evento.objects.create(
        nombre="Muda",
        fecha="2025-04-06",
        tipo="Ensayo",
        cofradia=cofradia_demo
    )

    evento3 = Evento.objects.create(
        nombre="Reunión General",
        fecha="2025-03-30",
        tipo="Reunión",
        cofradia=cofradia_demo
    )

    # Crear Tareas de ejemplo
    tarea1 = Tarea.objects.create(
        titulo="Revisión de Inventario",
        descripcion="Revisar el estado de los materiales de la Cofradía.",
        asignado_a="Juan Pérez",
        fecha_limite="2025-03-11",
        estado="Pendiente",
        prioridad="Alta",
        cofradia=cofradia_demo
    )

    tarea2 = Tarea.objects.create(
        titulo="Recaudación de Fondos",
        descripcion="Realizar una colecta para el mantenimiento de la Cofradía.",
        asignado_a="Ana López",
        fecha_limite="2025-03-20",
        estado="Pendiente",
        prioridad="Media",
        cofradia=cofradia_demo
    )

    tarea3 = Tarea.objects.create(
        titulo="Limpieza de la Iglesia",
        descripcion="Realizar una limpieza profunda en la iglesia de la Cofradía.",
        asignado_a="Carlos Martínez",
        fecha_limite="2025-04-01",
        estado="Pendiente",
        prioridad="Baja",
        cofradia=cofradia_demo
    )

    tarea4 = Tarea.objects.create(
        titulo="Organización de la Procesión",
        descripcion="Coordinar los detalles logísticos para la procesión de Semana Santa.",
        asignado_a="Lucía Fernández",
        fecha_limite="2025-04-05",
        estado="Pendiente",
        prioridad="Alta",
        cofradia=cofradia_demo
    )

    # Crear Inventario de ejemplo
    inventario1 = Inventario.objects.create(
        nombre="Cruz de Procesión",
        descripcion="Cruz que se lleva durante la procesión.",
        cantidad_disponible=5,
        ubicacion="Almacén Cofradía",
        cofradia=cofradia_demo
    )

    inventario2 = Inventario.objects.create(
        nombre="Velas",
        descripcion="Velas para las celebraciones.",
        cantidad_disponible=50,
        ubicacion="Almacén Cofradía",
        cofradia=cofradia_demo
    )

    inventario3 = Inventario.objects.create(
        nombre="Banderines",
        descripcion="Banderines para la procesión.",
        cantidad_disponible=10,
        ubicacion="Almacén Cofradía",
        cofradia=cofradia_demo
    )

    # Crear Préstamos de ejemplo
    prestamo1 = Prestamo.objects.create(
        hermano=hermano1,
        inventario=inventario1,
        estado_material="En buen estado",
        comentario="Prestado para la procesión",
        fianza="50 EUR"
    )

    prestamo2 = Prestamo.objects.create(
        hermano=hermano2,
        inventario=inventario2,
        estado_material="En buen estado",
        comentario="Prestado para el evento de la Semana Santa",
        fianza="30 EUR"
    )

    prestamo3 = Prestamo.objects.create(
        hermano=hermano1,
        inventario=inventario3,
        estado_material="En buen estado",
        comentario="Prestado para la procesión",
        fianza="40 EUR"
    )
"""

"""