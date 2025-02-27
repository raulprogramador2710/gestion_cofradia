# gestion_cofradia/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .views import informes, descargar_hermanos_pdf, descargar_hermanos_mayores_pdf

urlpatterns = [
    path('', lambda request: redirect('/inicio/')),  # Redirige "/" a "/inicio/"
    path('login/', auth_views.LoginView.as_view(template_name='gestion_cofradia/login.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),  # Ruta para cerrar sesión

    path('inicio/', views.inicio, name='inicio'),  # Página de inicio
    path('hermanos/', views.listar_hermanos, name='listar_hermanos'),
    path('informes/', views.informes, name='informes'),
    path('gestion-economica/', views.gestion_economica, name='gestion_economica'),

    path('hermanos/nuevo/', views.crear_hermano, name='crear_hermano'),
    path('hermanos/<int:pk>/', views.detalle_hermano, name='detalle_hermano'),
    path('usuarios/nuevo/', views.registrar_usuario, name='registrar_usuario'),
    path('hermanos/editar/<int:pk>/', views.editar_hermano, name='editar_hermano'),
    path('hermanos/eliminar/<int:pk>/', views.eliminar_hermano, name='eliminar_hermano'),

    path('informes/', informes, name='informes'),
    path('informes/hermanos/todos/', descargar_hermanos_pdf, name='descargar_hermanos_pdf'),
    path('informes/hermanos/mayores/', descargar_hermanos_mayores_pdf, name='descargar_hermanos_mayores_pdf'),

]
