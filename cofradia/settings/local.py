from .base import *
from celery.schedules import crontab

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'gestion_cofradia',  
        'USER': 'postgres', 
        'PASSWORD': 'Frakyx_es10',  
        'HOST': 'localhost',  
        'PORT': '5432', 
    }
}

INSTALLED_APPS += ["debug_toolbar"]  # Ejemplo de app solo para desarrollo

MIDDLEWARE.insert(1, "debug_toolbar.middleware.DebugToolbarMiddleware")

CELERY_BROKER_URL = 'redis://localhost:6379/0'  # Puedes usar Redis o RabbitMQ

CELERY_BEAT_SCHEDULE = {
    'recordatorio_evento_diario': {
        'task': 'core.tasks.recordatorio_evento',
        'schedule': crontab(minute=0, hour=9),  # Esto ejecutará la tarea todos los días a las 9 AM
    },
}