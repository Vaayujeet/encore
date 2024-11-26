"""Logging Settings for Correlator"""

import logging  # pylint: disable=unused-import # NOQA

from django.utils.log import (  # pylint: disable=unused-import # NOQA
    AdminEmailHandler,
    RequireDebugFalse,
    RequireDebugTrue,
)

CORRELATOR_LOG_LEVEL = logging.INFO

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        },
    },
    "formatters": {
        "correlator": {
            "format": "[{asctime}: {levelname}/{module}] [{process:d} {thread:d}] {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "level": CORRELATOR_LOG_LEVEL,
            "filters": ["require_debug_true"],
            "class": "logging.StreamHandler",
            "formatter": "correlator",
        },
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
        },
    },
    "loggers": {
        "correlator": {
            "handlers": ["console", "mail_admins"],
            "level": CORRELATOR_LOG_LEVEL,
        },
    },
}
