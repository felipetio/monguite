"""
Django CI/testing settings for monguite project.

These settings are optimized for CI/CD pipelines and automated testing.
"""

from .base import *

# SECURITY WARNING: This is acceptable for CI - not for production!
DEBUG = False

# Allow test runner to work
ALLOWED_HOSTS = ["*"]

# Faster password hashing for tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Use faster test database settings
DATABASES["default"]["CONN_MAX_AGE"] = 0
DATABASES["default"]["OPTIONS"] = {
    # Speed up tests - acceptable for CI where data loss is not a concern
    "options": "-c fsync=off -c synchronous_commit=off -c full_page_writes=off",
}

# Disable migrations for faster test runs (handled by pytest-django --reuse-db flag)
# Tests should use --nomigrations flag

# Logging - minimal for CI
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
}
