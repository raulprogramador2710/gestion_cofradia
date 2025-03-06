from .base import *
import dj_database_url
import logging

DEBUG = False

ALLOWED_HOSTS = ["gestion-cofradia-6byp.onrender.com"]

DATABASES = {
    "default": dj_database_url.config(default=os.getenv("DATABASE_URL"))
}

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

CSRF_TRUSTED_ORIGINS = ["https://gestion-cofradia-6byp.onrender.com"]

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("debug.log"),  # Guarda en un archivo
        logging.StreamHandler()  # Muestra en consola (Render logs)
    ]
)