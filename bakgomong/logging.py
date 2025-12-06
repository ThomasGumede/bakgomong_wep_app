import os
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent

# create logs dir robustly
LOGGING_DIR = BASE_DIR / "logs"
LOGGING_DIR.mkdir(parents=True, exist_ok=True)

# make level configurable via env var (default INFO in prod you'd raise to WARNING/ERROR)
LOGGING_LEVEL = os.getenv("LOGGING_LEVEL", "INFO").upper()

# rotation config
LOG_MAX_BYTES = int(os.getenv("LOG_MAX_BYTES", 10 * 1024 * 1024))  # 10MB
LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", 7))

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '%(levelname)s %(asctime)s %(name)s %(process)d %(threadName)s %(module)s %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'handlers': {
        'console': {
            'level': LOGGING_LEVEL,
            'class': 'logging.StreamHandler',
            'formatter': 'default',
        },
        'rotating_file': {
            'level': LOGGING_LEVEL,
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(LOGGING_DIR / 'app.log'),
            'maxBytes': LOG_MAX_BYTES,
            'backupCount': LOG_BACKUP_COUNT,
            'formatter': 'default',
        },
        # per-area rotating handlers
        'accounts_file': {
            'level': LOGGING_LEVEL,
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(LOGGING_DIR / 'accounts.log'),
            'maxBytes': LOG_MAX_BYTES,
            'backupCount': LOG_BACKUP_COUNT,
            'formatter': 'default',
        },
        'emails_file': {
            'level': LOGGING_LEVEL,
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(LOGGING_DIR / 'emails.log'),
            'maxBytes': LOG_MAX_BYTES,
            'backupCount': LOG_BACKUP_COUNT,
            'formatter': 'default',
        },
        'tasks_file': {
            'level': LOGGING_LEVEL,
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(LOGGING_DIR / 'tasks.log'),
            'maxBytes': LOG_MAX_BYTES,
            'backupCount': LOG_BACKUP_COUNT,
            'formatter': 'default',
        },
        'signals_file': {
            'level': LOGGING_LEVEL,
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(LOGGING_DIR / 'signals.log'),
            'maxBytes': LOG_MAX_BYTES,
            'backupCount': LOG_BACKUP_COUNT,
            'formatter': 'default',
        },
        'smtp_file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(LOGGING_DIR / 'smtp.log'),
            'maxBytes': LOG_MAX_BYTES,
            'backupCount': LOG_BACKUP_COUNT,
            'formatter': 'default',
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': True,
        },
    },
    'loggers': {
        # capture Django internals
        'django': {
            'handlers': ['console', 'rotating_file'],
            'level': LOGGING_LEVEL,
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console', 'rotating_file', 'mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
        # application-specific loggers
        'accounts': {
            'handlers': ['accounts_file', 'console'],
            'level': LOGGING_LEVEL,
            'propagate': False,
        },
        'emails': {
            'handlers': ['emails_file'],
            'level': LOGGING_LEVEL,
            'propagate': False,
        },
        'tasks': {
            'handlers': ['tasks_file'],
            'level': LOGGING_LEVEL,
            'propagate': False,
        },
        'signals': {
            'handlers': ['signals_file'],
            'level': LOGGING_LEVEL,
            'propagate': False,
        },
        # keep smtplib debug logs separate
        'smtplib': {
            'handlers': ['smtp_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
    # root logger fallback
    'root': {
        'handlers': ['console', 'rotating_file'],
        'level': LOGGING_LEVEL,
    },
}

