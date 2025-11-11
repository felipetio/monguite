# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Monguite is a Django web application for managing and tracking indigenous land data, including countries, states, biomes, and land categories. The project focuses on Brazilian indigenous territories with integration to external data sources (ISA - Instituto Socioambiental).

## Development Setup

**Dependencies**: This project uses Poetry for dependency management.

```bash
# Install dependencies
poetry install

# Activate virtual environment
poetry shell

# Copy environment file and configure
cp .env.example .env
# Edit .env to set SECRET_KEY, DATABASE_URL, and REDIS_URL
```

**Database**: PostgreSQL is required. Redis is used for caching.

```bash
# Run migrations
python manage.py migrate

# Load fixtures (sample data)
python manage.py loaddata fixtures.json

# Create superuser for admin access
python manage.py createsuperuser
```

## Common Commands

**Running the development server**:
```bash
python manage.py runserver
```

**Testing**:
```bash
# Run all tests
pytest

# Run specific test file
pytest app/tests.py

# Run with coverage
coverage run -m pytest
coverage report
```

**Database operations**:
```bash
# Create migrations after model changes
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Django shell for interactive testing
python manage.py shell_plus  # Requires django-extensions
```

**Code quality**:
```bash
# Format code with black
black .

# Sort imports
isort .

# Lint with flake8
flake8

# Run all pre-commit hooks
pre-commit run --all-files
```

## Project Structure

**Settings module**: `config/settings.py` - Django settings are in the `config` directory, not a typical project-named directory. The settings module uses `django-environ` for environment-based configuration.

**Main app**: `app/` - Single Django app containing all models, views, and admin configuration.

**Models hierarchy**:
- `Country` - Top-level geographic entity with language and codes
- `State` - Belongs to Country
- `Biome` - Ecological regions with area tracking (belongs to Country)
- `Land` - Indigenous territories with category classification (belongs to State and Biome)

**Admin customization**: The Django admin (`app/admin.py`) has significant customization:
- `BiomeAdmin` - Shows calculated preservation rates and related lands count
- `LandAdmin` - Includes external ISA link generation for lands with `isa_id`

**URL structure**:
- Root URLs in `config/urls.py`
- App-specific URLs in `app/urls.py`
- Admin at `/admin/`
- Debug toolbar at `/__debug__/` (development only)

## Key Technical Details

**Database**: The project uses PostgreSQL with atomic requests enabled (`ATOMIC_REQUESTS = True`). Each request is wrapped in a transaction.

**Caching**: Redis cache configured with `django_redis` backend. Exception handling mimics memcache behavior (ignores exceptions).

**External integration**: Land model contains `isa_id` field for linking to terrasindigenas.org.br external database.

**Land categories**: Four indigenous land categories defined in `Land.CATEGORY_CHOICES`:
- DI: Dominial Indígena
- PI: Parque Indígena
- RI: Reserva Indígena
- TI: Terra Indígena

## Code Standards

**Linting configuration** (setup.cfg):
- Max line length: 120 characters
- Excludes: migrations, static cache, docs, node_modules, venv

**Pre-commit hooks**: Configured to run on push (not commit). Includes:
- black (code formatting)
- isort (import sorting)
- flake8 (linting with isort integration)
- Standard pre-commit hooks (trailing whitespace, debug statements, private key detection, etc.)

**Testing**: pytest-django is configured to use `config.settings` and reuse database between test runs for performance.
