"""
Django settings for portfolio project.
Configured for Render + Neon DB deployment.
"""

from pathlib import Path
import os
import dj_database_url
from django.core.exceptions import ImproperlyConfigured

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# --- PRODUCTION SECURITY ---
# Automatically turns off DEBUG mode when running on Render
DEBUG = os.getenv('DJANGO_DEBUG', 'False').strip().lower() in {'1', 'true', 'yes'}

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    if not DEBUG:
        raise ImproperlyConfigured('DJANGO_SECRET_KEY must be configured when DEBUG is disabled.')
    SECRET_KEY = 'django-insecure-local-development-only'
elif not DEBUG and (len(SECRET_KEY) < 50 or SECRET_KEY.startswith('django-insecure-')):
    raise ImproperlyConfigured('DJANGO_SECRET_KEY must be a strong, randomly generated key in production.')

ALLOWED_HOSTS = [
    h.strip() for h in os.getenv('DJANGO_ALLOWED_HOSTS', '').split(',') if h.strip()
]

# Automatic fallback for your Render deployment domain
if not DEBUG:
    ALLOWED_HOSTS.append('aryan-pawar.onrender.com')

if DEBUG:
    ALLOWED_HOSTS.extend(['localhost', '127.0.0.1'])
elif not ALLOWED_HOSTS:
    raise ImproperlyConfigured('DJANGO_ALLOWED_HOSTS must contain the deployed host.')

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.getenv('DJANGO_CSRF_TRUSTED_ORIGINS', '').split(',')
    if origin.strip()
]

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = not DEBUG
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG


# --- APPLICATION DEFINITION ---
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    
    # WhiteNoise needs to be positioned above the core staticfiles app
    'whitenoise.runserver_nostatic', 
    'django.contrib.staticfiles',
    
    # Custom registered application
    'projects',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # WhiteNoise middleware to handle static files on Render
    'whitenoise.middleware.WhiteNoiseMiddleware', 
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'projects.middleware.PageViewTrackingMiddleware',  
]

ROOT_URLCONF = 'portfolio.urls'

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

WSGI_APPLICATION = 'portfolio.wsgi.application'


# --- DATABASE CONFIGURATION ---
database_url = os.getenv('DATABASE_URL')
if not DEBUG:
    if not database_url:
        raise ImproperlyConfigured('DATABASE_URL must be configured in production.')
    if not database_url.startswith(('postgres://', 'postgresql://')):
        raise ImproperlyConfigured('DATABASE_URL must use PostgreSQL in production.')

DATABASES = {
    'default': dj_database_url.config(
        default=database_url or f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
        conn_health_checks=True,
    )
}


# --- PASSWORD VALIDATION ---
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# --- INTERNATIONALIZATION ---
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True


# --- STATIC AND MEDIA ASSETS ---
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# WhiteNoise storage optimization (compresses and caches files)
STATICFILES_STORAGE_BACKEND = (
    'whitenoise.storage.CompressedStaticFilesStorage'
    if DEBUG else 'whitenoise.storage.CompressedManifestStaticFilesStorage'
)
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": STATICFILES_STORAGE_BACKEND,
    },
}

MEDIA_URL = '/media/'
MEDIA_ROOT = Path(os.getenv('DJANGO_MEDIA_ROOT', str(BASE_DIR / 'media')))

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# --- EMAIL CONFIGURATION ---
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('DJANGO_EMAIL_USER') 
EMAIL_HOST_PASSWORD = os.getenv('DJANGO_EMAIL_PASSWORD', os.getenv('HOST_PASSWORD', ''))
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
