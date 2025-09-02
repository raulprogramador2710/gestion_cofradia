from django.shortcuts import render
from django.urls import path
from django.contrib.auth.decorators import login_required
from django.contrib.auth import views as auth_views
from . import views

app_name = 'gestion_cofradia'


urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'), 
    path('inicio/', views.inicio, name='inicio'),

    #Hermanos
    path('hermanos/', views.lista_hermanos, name='lista_hermanos'),
    path('hermanos/json/', views.hermanos_json, name='hermanos_json'),
    path('hermanos/crear/', views.crear_hermano, name='crear_hermano'),
    path('hermanos/<int:pk>/', views.ver_hermano, name='ver_hermano'),
    path('hermanos/<int:pk>/editar/', views.editar_hermano, name='editar_hermano'),
    path("hermanos/<int:pk>/baja/", views.dar_de_baja_hermano, name="dar_baja_hermano"),

    path('hermanos/<int:pk>/notificar/', views.notificar_hermano, name='notificar_hermano'),
    path('hermanos/upload-csv/', views.upload_hermanos_csv, name='upload_hermanos_csv'),

    # Cuotas
    path('cuotas/', views.lista_cuotas, name='lista_cuotas'),
    path('cuotas/crear/', views.crear_cuota, name='crear_cuota'),
    path('cuotas/editar/<int:pk>/', views.editar_cuota, name='editar_cuota'),
    path('cuotas/eliminar/<int:pk>/', views.eliminar_cuota, name='eliminar_cuota'),

    # Pagos
    path('hermano/<int:hermano_pk>/pago/<int:cuota_pk>/', views.registrar_pago, name='registrar_pago'),
    path('hermano/<int:hermano_pk>/pagos/', views.lista_pagos_hermano, name='lista_pagos_hermano'),

    # Notificaciones
    path('notificaciones/', views.lista_notificaciones, name='lista_notificaciones'),
    path('notificaciones/crear/', views.crear_notificacion, name='crear_notificacion'),
    path('notificaciones/<int:pk>/', views.ver_notificacion, name='ver_notificacion'),
    path('notificaciones/<int:pk>/editar/', views.editar_notificacion, name='editar_notificacion'),
    path('notificaciones/<int:pk>/eliminar/', views.eliminar_notificacion, name='eliminar_notificacion'),

    #Tareas
    path('tareas/', views.lista_tareas, name='lista_tareas'),
    path('tareas/crear/', views.crear_tarea, name='crear_tarea'),
    path('tareas/<int:pk>/', views.ver_tarea, name='ver_tarea'),
    path('tareas/<int:tarea_id>/editar/', views.editar_tarea, name='editar_tarea'),
    path('tareas/<int:tarea_id>/completar/', views.completar_tarea, name='completar_tarea'),
    path("tareas/<int:pk>/eliminar/", views.eliminar_tarea, name="eliminar_tarea"),

    #Doumentacion
    path('documentos/', views.lista_documentos, name='lista_documentos'),
    path('documentos/crear/', views.crear_documento, name='crear_documento'),
    path('documentos/<int:documento_id>/', views.ver_documento, name='ver_documento'),
    path('documentos/<int:documento_id>/editar/', views.editar_documento, name='editar_documento'),
    path('documentos/<int:documento_id>/eliminar/', views.eliminar_documento, name='eliminar_documento'),
    #INFORMES
    path('documentos/informes/', views.lista_informes, name='lista_informes'),
    path('documentos/informes/descargar/<str:tipo>/', views.descargar_informe, name='descargar_informe'),

    #Eventos
    path('eventos/', views.lista_eventos, name='lista_eventos'),
    path('eventos/crear/', views.crear_evento, name='crear_evento'),
    path('eventos/<int:evento_id>/', views.ver_evento, name='ver_evento'),
    path('eventos/<int:evento_id>/editar/', views.editar_evento, name='editar_evento'),
    path('eventos/<int:evento_id>/eliminar/', views.eliminar_evento, name='eliminar_evento'),

    #Alquileres
    path('alquileres/', views.lista_alquileres, name='lista_alquileres'),
    path('alquileres/crear/', views.crear_alquiler, name='crear_alquiler'),
    path('alquileres/<int:pk>/', views.ver_alquiler, name='ver_alquiler'),
    path('alquileres/<int:pk>/editar/', views.editar_alquiler, name='editar_alquiler'),
    path('alquileres/<int:pk>/eliminar/', views.eliminar_alquiler, name='eliminar_alquiler'), 

    #Enseres
    path('enseres/', views.lista_enseres, name='lista_enseres'),
    path('enseres/crear/', views.crear_enser, name='crear_enser'),
    path('enseres/<int:pk>/', views.ver_enser, name='ver_enser'),
    path('enseres/<int:pk>/editar/', views.editar_enser, name='editar_enser'),
    path('enseres/<int:pk>/borrar/', views.borrar_enser, name='borrar_enser'),

    # Noticias
    path("noticias/", views.lista_noticias, name="lista_noticias"),
    path("noticias/nueva/", views.crear_noticia, name="crear_noticia"),
    path("noticias/<int:pk>/", views.ver_noticia, name="ver_noticia"),
    path("noticias/<int:pk>/editar/", views.editar_noticia, name="editar_noticia"),
    path("noticias/<int:pk>/eliminar/", views.eliminar_noticia, name="eliminar_noticia"),

]