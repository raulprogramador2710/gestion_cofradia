from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

app_name = 'portal_hermano'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.dashboard, name='dashboard'),

    path('datos-personales/', views.datos_personales, name='datos_personales'),
    path('error-no-hermano/', views.error_no_hermano, name='error_no_hermano'),

    path('tareas/', views.ver_tareas, name='ver_tareas'),

    path('eventos/', views.ver_eventos, name='eventos'),

    path('notificaciones/', views.notificaciones, name='notificaciones'),

    path('cuotas/', views.cuotas, name='cuotas'),

    path('documentos/', views.documentos, name='documentos'),

    path('cambiar_password/', views.cambiar_password, name='cambiar_password'),
]