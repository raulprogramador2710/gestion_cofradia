# wsgi.py
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofradia.settings')
os.system("python manage.py migrate --noinput")

application = get_wsgi_application()
