from django.urls import path
from . import views
from .views import inicio, CustomLoginView, enviar_correo
from .views import (
    informes_view,
    informe_hermanos_alfabetico,
    informe_mayores_edad,
    informe_cuotas_pendientes,
    informe_antiguedad,
    informe_eventos,
    informe_finanzas,
    informe_tareas_pendientes,
)

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),  # Ruta para cerrar sesión
    path('', inicio, name='inicio'),

    path('crear-hermano/', views.crear_hermano, name='crear_hermano'),
    path('lista-hermanos/', views.lista_hermanos, name='lista_hermanos'),
    path('detalle-hermanos/<int:pk>/', views.detalle_hermano, name='detalle_hermano'),
    path('editar-hermano/<int:pk>/', views.editar_hermano, name='editar_hermano'),
    path('eliminar-hermano/<int:pk>/', views.eliminar_hermano, name='eliminar_hermano'),

    path('crear-tarea/', views.crear_tarea, name='crear_tarea'),
    path('lista-tareas/', views.lista_tareas, name='lista_tareas'),
    path('detalle-tarea/<int:pk>/', views.detalle_tarea, name='detalle_tarea'),
    path('editar-tarea/<int:pk>/', views.editar_tarea, name='editar_tarea'),
    path('eliminar-tarea/<int:pk>/', views.eliminar_tarea, name='eliminar_tarea'),

    path('crear-evento/', views.crear_evento, name='crear_evento'),
    path('lista-eventos/', views.lista_eventos, name='lista_eventos'),
    path('detalle-evento/<int:pk>/', views.detalle_evento, name='detalle_evento'),
    path('editar-evento/<int:pk>/', views.editar_evento, name='editar_evento'),
    path('eliminar-evento/<int:pk>/', views.eliminar_evento, name='eliminar_evento'),

    path('informes/', informes_view, name='informes'),
    path('informes/hermanos-alfabetico/', informe_hermanos_alfabetico, name='informe_hermanos_alfabetico'),
    path('informes/hermanos-mayores/', informe_mayores_edad, name='informe_mayores_edad'),
    path('informes/cuotas-pendientes/', informe_cuotas_pendientes, name='informe_cuotas_pendientes'),
    path('informes/hermanos-antiguedad/', informe_antiguedad, name='informe_antiguedad'),
    path('informes/eventos-anuales/', informe_eventos, name='informe_eventos'),
    path('informes/finanzas/', informe_finanzas, name='informe_finanzas'),
    path('informes/tareas-pendientes/', informe_tareas_pendientes, name='informe_tareas_pendientes'),

    path('crear-inventario/', views.crear_inventario, name='crear_inventario'),
    path('lista-inventario/', views.lista_inventario, name='lista_inventario'),#primero vista despues menu
    path('detalle-inventario/<int:pk>/', views.detalle_inventario, name='detalle_inventario'),
    path('editar-inventario/<int:pk>/', views.editar_inventario, name='editar_inventario'),
    path('eliminar-inventario/<int:pk>/', views.eliminar_inventario, name='eliminar_inventario'),

    path('crear-prestamo/', views.crear_prestamo, name='crear_prestamo'),
    path('lista-prestamos/', views.lista_prestamos, name='lista_prestamos'),
    path('detalle-prestamo/<int:pk>/', views.detalle_prestamo, name='detalle_prestamo'),
    path('editar-prestamo/<int:pk>/', views.editar_prestamo, name='editar_prestamo'),
    path('eliminar-prestamo/<int:pk>/', views.eliminar_prestamo, name='eliminar_prestamo'),

    path('enviar-correo/', enviar_correo, name='enviar_correo'),

    path('configuracion/', views.configuracion, name='configuracion'),  # Vista de configuración
    path('configuracion/cargar-hermanos/', views.cargar_hermanos, name='cargar_hermanos'),  # Vista de carga masiva
]
