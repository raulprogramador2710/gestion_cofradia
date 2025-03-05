# base.py
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.getenv('SECRET_KEY', 'your_default_secret_key')
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost').split(',')
INSTALLED_APPS = [
    # Aplicaciones predeterminadas de Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Tus aplicaciones
    'apps.gestion_cofrade',
    'apps.app_informativa',
    'apps.acceso_hermanos',
    'apps.web_hermandad',
    # Otras aplicaciones
    'widget_tweaks',
]
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'app.gestion_cofradia.middleware.CurrentUserMiddleware',
]
ROOT_URLCONF = 'cofradia.urls'
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]
WSGI_APPLICATION = 'cofradia.wsgi.application'
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'gestion_cofradia'),
        'USER': os.getenv('DB_USER', 'gestion_cofradia_user'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'your_db_password'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': '5432',
    }
}
