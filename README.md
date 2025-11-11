# Monguite

Django app for managing Brazilian indigenous land data.

## Quick Start

```bash
# Install dependencies
poetry install

# Start database services
docker compose up -d

# Run migrations and load data
poetry run python manage.py migrate
poetry run python manage.py loaddata fixtures.json

# Start the server
poetry run python manage.py runserver
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
pytest

# Code quality
black .
isort .
flake8
```

## License

GPLv3
