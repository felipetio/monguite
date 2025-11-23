#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Collect static files for the Django application
uv run python manage.py collectstatic --noinput
