import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

if os.environ.get("DJANGO_ENV", "dev").lower() == "prod":
    from config.settings.prod import *
else:
    from config.settings.dev import *
