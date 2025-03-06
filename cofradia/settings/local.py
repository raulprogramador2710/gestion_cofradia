from .base import *

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
