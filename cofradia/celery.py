# mi_proyecto/celery.py
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Establecer el módulo de configuración predeterminado para 'celery'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mi_proyecto.settings')

app = Celery('mi_proyecto')

# Usando una cadena para evitar la necesidad de deserializar el objeto
app.config_from_object('django.conf:settings', namespace='CELERY')

# Cargar tareas de todos los módulos de aplicación registrados
app.autodiscover_tasks()
