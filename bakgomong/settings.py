import os, re
from pathlib import Path
from bakgomong.logging import LOGGING
from decouple import config, Csv
from celery.schedules import crontab

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET', 'django-insecure-^9#-e&z484&v&)(iime^im_3(q#%tzpaojm#87lk$1-_tq)8(0')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'admin_interface',
    'colorfield',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    'accounts.apps.AccountsConfig',
    'contributions',
    
    'tinymce',
    'django_celery_beat',
    'django_celery_results',
]

X_FRAME_OPTIONS = "SAMEORIGIN"
SILENCED_SYSTEM_CHECKS = ["security.W019"]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'bakgomong.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'bakgomong.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'bakgomongdb',
            'USER': config("DB_USER"),
            'PASSWORD': config("DB_PASSWORD"),
            'HOST': 'localhost',
            'PORT': '5432',
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

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Africa/Johannesburg'

USE_I18N = True

USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Database & Static
if DEBUG:
    ALLOWED_HOSTS = []
    
    STATIC_URL = 'static/'
    STATICFILES_DIRS = [
        BASE_DIR / 'static'
    ]
    STATIC_ROOT = os.path.join(BASE_DIR, 'static_root')
    YOCO_SECRET_KEY = config('YOCO_TEST_API_KEY')
else:
    ALLOWED_HOSTS = ['bakgomong.co.za', 'www.bakgomong.co.za', 'localhost']
    CSRF_TRUSTED_ORIGINS = ['https://127.0.0.1', 'https://localhost', 'https://bakgomong.co.za', 'https://www.bakgomong.co.za']
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    X_FRAME_OPTIONS = "SAMEORIGIN"
    YOCO_SECRET_KEY = config('YOCO_TEST_API_KEY')

    # SSL SETTINGS
    
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    
    STATIC_URL = 'static/'
    STATIC_ROOT = os.path.join(BASE_DIR, 'static')
    
    SILENCED_SYSTEM_CHECKS = ['security.W019']
    ADMINS = [
    ("Wandile Gumede", "bakgomongs@gmail.com"),
    ]
    MANAGERS = [('admin@bakgomong.co.za', 'bakgomongs@gmail.com'), ('support@bakgomong.co.za',)]

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Celery
CELERY_BROKER_URL = 'redis://127.0.0.1:6379/0'
BROKER_URL = 'redis://127.0.0.1:6379/0'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_TASK_TIME_LIMIT = 30 * 60
CELERY_RESULT_EXTENDED = True
CELERY_worker_state_db = True
CELERY_result_persistent = True
CELERY_RESULT_BACKEND = 'django-db'
CELERY_TIMEZONE = 'Africa/Johannesburg'
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers.DatabaseScheduler'

CELERY_BROKER_TRANSPORT_OPTIONS = {'visibility_timeout': 3600}  # Optional, for timeout adjustments
CELERY_TASK_IGNORE_RESULT = True
CELERY_ACKS_LATE = True  # Ensures tasks are acknowledged after execution
CELERY_RETRY_POLICY = {
    'max_retries': 3,
    'interval_start': 0,
    'interval_step': 0.2,
    'interval_max': 0.5,
}

# Tailwind
INSTALLED_APPS += ['tailwind', 'theme']
TAILWIND_APP_NAME = 'theme'
NPM_BIN_PATH = "npm.cmd"
INTERNAL_IPS = [
    "127.0.0.1", '0.0.0.0'
]

# Tiny
TINYMCE_DEFAULT_CONFIG = {
    'content_style': '* { margin: 0 !important; padding: 0 !important; }',
    'theme_advanced_fonts': 'DM Sans=dm-sans,Arial=arial,helvetica,sans-serif',
    'height': "400px",
    'cleanup_on_startup': True,
    'custom_undo_redo_levels': 20,
    'images_upload_url': '/tinymce-upload/',
    'automatic_uploads': True,
    'file_picker_types': 'image',
    'file_picker_callback': """
        function (cb, value, meta) {
            if (meta.filetype === 'image') {
                var input = document.createElement('input');
                input.setAttribute('type', 'file');
                input.setAttribute('accept', 'image/*');
                input.onchange = function () {
                    var file = this.files[0];
                    var formData = new FormData();
                    formData.append('file', file);
                    fetch('/tinymce-upload/', {
                        method: 'POST',
                        body: formData
                    })
                    .then(response => response.json())
                    .then(data => {
                        cb(data.location, { title: file.name });
                    })
                    .catch(err => console.error(err));
                };
                input.click();
            }
        }
    """,
    "menubar": "file edit view insert format tools table help",
    "plugins": "advlist autolink lists link image charmap print preview anchor searchreplace visualblocks fullscreen insertdatetime media table paste help",
    "toolbar": "undo redo | bold italic underline strikethrough | fontselect fontsizeselect formatselect | alignleft aligncenter alignright alignjustify | outdent indent | numlist bullist checklist | forecolor backcolor casechange permanentpen formatpainter removeformat | pagebreak | charmap emoticons | fullscreen preview save print | a11ycheck ltr rtl | showcomments addcomment",
}


AUTH_USER_MODEL = 'accounts.Account'
AUTHENTICATION_BACKENDS = ['accounts.utils.backends.EmailBackend']
LOGIN_URL = 'accounts:login'


# Email
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'mail.bakgomong.co.za'
EMAIL_PORT = 465
EMAIL_USE_TLS = False
EMAIL_USE_SSL = True
EMAIL_HOST_USER = 'noreply@bakgomong.co.za'
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = 'BAKMGOMONG <noreply@bakgomong.co.za>'
SERVER_EMAIL = DEFAULT_FROM_EMAIL


SMSPORTAL_AUTH=config('Client_ID')
TWILIO_SID=config('TWILIO_SID')
TWILIO_AUTH_TOKEN=config('TWILIO_AUTH_TOKEN')
TWILIO_FROM='+12067456246'

if DEBUG:
    SITE_URL = "http://127.0.0.1:8000"
else:
    SITE_URL = "https://bakgomong.co.za"

INSTALLED_APPS += [
    "django_q",
]

# Example: ORM broker (no external service)
Q_CLUSTER = {
    "name": "bakgomong",
    "workers": 4,
    "recycle": 500,
    "timeout": 60,
    "retry": 120,
    "queue_limit": 50,
    "bulk": 10,
    "orm": "default",
}

# settings.py
BULKSMS_USERNAME = config('BULKSMS_USERNAME', default='your_username')
BULKSMS_PASSWORD = config('BULKSMS_PASSWORD', default='your_password')
BULKSMS_SENDER = config('BULKSMS_SENDER', default='BAKGOMONG')
