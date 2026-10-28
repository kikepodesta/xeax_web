

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load variables from .env / .env.prod (no dependencies needed).
# .env.prod takes precedence for keys defined in both files.
for _fname in ('.env.prod', '.env'):
    _env_file = BASE_DIR / _fname
    if _env_file.exists():
        for _line in _env_file.read_text().splitlines():
            _line = _line.strip()
            if _line and not _line.startswith('#') and '=' in _line:
                _key, _, _value = _line.partition('=')
                os.environ.setdefault(_key.strip(), _value.strip().strip('"').strip("'"))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-(mt2==1%!y@ao-tppdd_piu&l23q3y=pxxip62s*udr3!t=qbp')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'True').lower() in ('1', 'true', 'yes')

ALLOWED_HOSTS = [h.strip() for h in os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',') if h.strip()]

CSRF_TRUSTED_ORIGINS = [o.strip() for o in os.environ.get('CSRF_TRUSTED_ORIGINS', '').split(',') if o.strip()]

# The app sits behind the Nginx reverse proxy that terminates TLS
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'main_app',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'main_app.middleware.ActivityLoggerMiddleware',
]

ROOT_URLCONF = 'xeax_sports_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
                'main_app.context_processors.cart_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'xeax_sports_project.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'xeax_db'),
        'USER': os.environ.get('DB_USER', 'xeaxuser'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'xeaxPuser'),
        'HOST': os.environ.get('DB_HOST', '127.0.0.1'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/


LANGUAGE_CODE = 'es'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

LANGUAGES = [
    ('es', 'Español'),
    ('en', 'English'),
    ('it', 'Italiano'),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'

STATICFILES_DIRS = [
    BASE_DIR / 'assets',
]

STATIC_ROOT = BASE_DIR / 'staticfiles'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Authentication
LOGIN_URL = 'main_app:login'
LOGIN_REDIRECT_URL = 'main_app:home'

# Media files (uploads)
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Google OAuth2 Credentials
GOOGLE_CLIENT_ID = 'placeholder-google-client-id'
GOOGLE_CLIENT_SECRET = 'placeholder-google-client-secret'

# -------------------------------------------------------
# Email — SMTP IONOS. Si no hay contraseña configurada
# (variable de entorno XEAX_EMAIL_PASSWORD), se usa la
# consola para no romper el desarrollo local.
# -------------------------------------------------------
EMAIL_HOST = 'smtp.ionos.es'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'noreply@xeaxsports.com'
EMAIL_HOST_PASSWORD = os.environ.get('XEAX_EMAIL_PASSWORD', '')
DEFAULT_FROM_EMAIL = 'XEAX Sports <noreply@xeaxsports.com>'
SERVER_EMAIL = DEFAULT_FROM_EMAIL

if EMAIL_HOST_PASSWORD:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# URL pública del sitio (se usa en enlaces de emails enviados
# desde signals, donde no hay request). En producción definir
# la variable de entorno XEAX_SITE_URL.
SITE_URL = os.environ.get('XEAX_SITE_URL', 'http://localhost:8000')
# Cookies seguras
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True