# Monguite

Django app for managing Brazilian indigenous land data.

## Quick Start

```bash
# Install dependencies
uv sync

# Start database services
docker compose up -d

# Run migrations and load data
uv run python manage.py migrate
uv run python manage.py loaddata fixtures.json

# Start the server
uv run python manage.py runserver
```

Visit http://localhost:8000/admin

Default login: `admin` / `admin`

## What's Inside

- 1 Country (Brazil)
- 27 States
- 7 Biomes
- Land tracking with categories (DI, PI, RI, TI)

## Tech Stack

- Python 3.13
- Django 5.2
- PostgreSQL 16
- Redis 7

## Development

```bash
# Tests
uv run pytest

# Code quality
uv run black .
uv run isort .
uv run flake8
```

## License

GPLv3
