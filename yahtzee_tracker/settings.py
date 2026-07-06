"""
Django settings for yahtzee_tracker project.
"""

import os
import sys
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load a local .env file for development. On Fly.io there is no .env file and
# secrets come from the environment directly.
if os.path.exists(BASE_DIR / ".env"):
    load_dotenv(BASE_DIR / ".env")


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

# Hide the admin under a non-default path in production. Default stays /admin/.
ADMIN_URL = os.environ.get("ADMIN_URL", "admin/")
if not ADMIN_URL.endswith("/"):
    ADMIN_URL = f"{ADMIN_URL}/"

# Content Security Policy. HTMX is vendored in static/js, so script-src only needs
# 'self'. Inline styles and event handlers still require 'unsafe-inline'.
CSP_HEADER = "; ".join(
    [
        "default-src 'self'",
        "script-src 'self' 'unsafe-inline'",
        "style-src 'self' 'unsafe-inline'",
        "connect-src 'self'",
        "form-action 'self'",
        "frame-ancestors 'none'",
    ]
)


def CSP_MIDDLEWARE(get_response):
    """Attach a basic Content-Security-Policy header to all responses."""

    def middleware(request):
        response = get_response(request)
        response["Content-Security-Policy"] = CSP_HEADER
        return response

    return middleware


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
    "yahtzee_tracker.settings.CSP_MIDDLEWARE",
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


# --- Caching ----------------------------------------------------------------

# LocMemCache is enough for django-ratelimit on a single Machine. If the app is
# ever scaled beyond one Machine, switch to a shared cache (e.g. Redis).
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}


# --- Rate limiting ----------------------------------------------------------

# LocMemCache is fine because the Fly.io deployment is scaled to a single
# Machine. If that ever changes, switch to a shared cache backend.
RATELIMIT_USE_CACHE = "default"
RATELIMIT_VIEW = "yahtzee_tracker.views.ratelimited_429"


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


# --- Logging ----------------------------------------------------------------

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "{asctime} {levelname} {name}: {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}
