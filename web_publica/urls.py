# urls.py para la aplicación web_publica
from django.urls import path
from . import views

app_name = 'web_publica'

urlpatterns = [
    # Página principal
    path('', views.inicio, name='inicio'),
    path("hazte-hermano/", views.hazte_hermano, name="hazte_hermano"),
    path("noticias/", views.noticias, name="noticias"),
    path("noticias/<int:id>/", views.noticia_detalle, name="noticia_detalle"),
    # Historia Cofradía
    path("historia/", views.historia_cofradia, name="historia_cofradia"),

    # Titulares
    path("titulares/cristo-expiracion/", views.titular_cristo, name="titular_cristo"),
    path("titulares/virgen-dolores/", views.titular_virgen, name="titular_virgen"),
]