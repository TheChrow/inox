# inox — imagen Django con WeasyPrint y mysqlclient.
# Una sola imagen sirve para prod (gunicorn) y dev (runserver); el comando
# concreto vive en docker-compose.yml / docker-compose.dev.yml.

FROM python:3.12-alpine

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Deps de sistema:
#  - mysql-dev + libffi-dev + libc-dev + build-base: compilar mysqlclient
#  - cairo + pango + gdk-pixbuf + harfbuzz + fribidi + fontconfig + ttf-freefont:
#    runtime de WeasyPrint
#  - libintl + libuuid: requeridos transitivamente por cairo/pango
RUN apk add --no-cache \
        mysql-dev \
        mariadb-connector-c \
        python3-dev \
        libc-dev \
        libffi-dev \
        cairo \
        pango \
        gdk-pixbuf \
        harfbuzz \
        fribidi \
        fontconfig \
        ttf-freefont \
        libintl \
        libuuid \
        build-base \
    && pip install --upgrade pip

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Generar caché de fuentes y soltar el toolchain para achicar la imagen
RUN fc-cache -f && apk del build-base

COPY . .

EXPOSE 8000

# Sin CMD: cada servicio en docker-compose define el comando concreto
# (gunicorn en prod, runserver en dev). Evita defaults que confunden.
