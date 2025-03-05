from django.urls import path
from . import views
from .views import inicio, CustomLoginView

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

    path('configuracion/', views.configuracion, name='configuracion'),  # Vista de configuración
    path('configuracion/cargar-hermanos/', views.cargar_hermanos, name='cargar_hermanos'),  # Vista de carga masiva
]
