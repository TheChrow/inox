import os 
from config.settings.base import *

EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")
SECRET_KEY = os.environ.get("SECRET_KEY")
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

DEBUG = False
ALLOWED_HOSTS = get_required_env_list("ALLOWED_HOSTS_PROD")

STATIC_ROOT = Path.joinpath(BASE_DIR, "staticfiles")
#STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"

STATIC_URL = "/static/"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"