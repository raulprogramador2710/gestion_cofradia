"""
WSGI config for gestion_cofradia project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/wsgi/
"""

import os
from django.core.wsgi import get_wsgi_application

# Aquí se especifica el archivo de configuración de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_cofradia.settings')

# Se crea la aplicación WSGI que será usada por Gunicorn
application = get_wsgi_application()
