import os
from config.settings.base import *


SECRET_KEY = os.environ.get("SECRET_KEY")
DEBUG = True

ALLOWED_HOSTS = get_required_env_list("ALLOWED_HOSTS_DEVELOP")
STATIC_ROOT = Path.joinpath(BASE_DIR, "staticfiles")
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
