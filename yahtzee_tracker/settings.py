"""
Django settings for yahtzee_tracker project.
"""

import os
import sys
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# --- Security settings ------------------------------------------------------

SECRET_KEY = os.environ.get("SECRET_KEY")
IS_TESTING = "test" in sys.argv
if not SECRET_KEY:
    if IS_TESTING:
        SECRET_KEY = "test-secret-key-not-for-production"
    else:
        raise ImproperlyConfigured("SECRET_KEY environment variable is required.")

DEBUG = os.environ.get("DEBUG", "").lower() in ("true", "1", "yes")

_allowed_hosts = os.environ.get("ALLOWED_HOSTS", "")
if _allowed_hosts:
    ALLOWED_HOSTS = [host.strip() for host in _allowed_hosts.split(",") if host.strip()]
else:
    ALLOWED_HOSTS = ["localhost", "127.0.0.1"] if not DEBUG else []

# Allow the deployed HTTPS origin for POST/CSRF requests.
CSRF_TRUSTED_ORIGINS = [f"https://{host}" for host in ALLOWED_HOSTS if "." in host]

# Trust Fly.io's X-Forwarded-Proto header only in production, never on a dev box.
if not DEBUG and any("." in host for host in ALLOWED_HOSTS):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Production-only HTTPS hardening. Skip SSL redirect during tests so the test
# client does not get 301'd to HTTPS on every request.
if not DEBUG and not IS_TESTING:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"


# --- Application definition ------------------------------------------------

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "users",
    "games",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "yahtzee_tracker.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "yahtzee_tracker.wsgi.application"


# --- Database ---------------------------------------------------------------

# Allow overriding the SQLite path via environment variable so Docker can mount
# the database into a persistent volume.
DATABASE_PATH = os.environ.get("DATABASE_PATH", BASE_DIR / "db.sqlite3")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": DATABASE_PATH,
    }
}


# --- Password validation -----------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# --- Authentication redirects -----------------------------------------------

LOGIN_REDIRECT_URL = "/games/"
LOGOUT_REDIRECT_URL = "/games/"

# --- Internationalization ---------------------------------------------------

LANGUAGE_CODE = "de-de"

TIME_ZONE = "Europe/Berlin"

USE_I18N = True

USE_TZ = True


# --- Static files -----------------------------------------------------------

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
