from .base import *
import dj_database_url

DEBUG = False

ALLOWED_HOSTS = ["gestion-cofradia-6byp.onrender.com"]

DATABASES = {
    "default": dj_database_url.config(default=os.getenv("DATABASE_URL"))
}

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

CSRF_TRUSTED_ORIGINS = ["https://gestion-cofradia-6byp.onrender.com"]

STATICFILES_STORAGE = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"

MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")
