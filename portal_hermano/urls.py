from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

app_name = 'portal_hermano'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    path('', views.dashboard, name='dashboard'),

    path('datos-personales/', views.datos_personales, name='datos_personales'),
    path('error-no-hermano/', views.error_no_hermano, name='error_no_hermano'),

    path('tareas/', views.ver_tareas, name='ver_tareas'),
    path('eventos/', views.ver_eventos, name='ver_eventos'),

    path('notificaciones/', views.ver_notificaciones, name='ver_notificaciones'),
    path('cuotas/', views.ver_cuotas, name='ver_cuotas'),
    path('documentos/', views.ver_documentos, name='ver_documentos'),

    path('password_change/', views.cambiar_password, name='cambiar_password'),

    path('password_reset/', auth_views.PasswordResetView.as_view( template_name='password/password_reset_form.html', extra_context={'base_template': 'base_portal_publica.html'}), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='password/password_reset_done.html', extra_context={'base_template': 'base_portal_publica.html'}), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='password/password_reset_confirm.html', extra_context={'base_template': 'base_portal_publica.html'}), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='password/password_reset_complete.html', extra_context={'base_template': 'base_portal_publica.html'}), name='password_reset_complete'),
]