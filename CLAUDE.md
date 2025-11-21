# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Monguite is a Django REST API application for managing and tracking indigenous land data, including countries, states, municipalities, biomes, and indigenous territories. The project focuses on Brazilian indigenous territories with integration to external data sources (ISA - Instituto Socioambiental).

## 🚨 Critical Rules

1. **ALL TESTS MUST PASS** - No task is complete until 100% of tests pass. No exceptions.
1. **ALWAYS make atomic commits** - One feature/fix per commit, never combine unrelated changes
1. **Run tests before committing** - Use `pytest` to run relevant tests before committing
1. **Run linters before committing** - Use `pre-commit run` to validate code quality
1. **Document as you code** - Update relevant docs in `docs/` as you make modifications
1. **Follow Django best practices** - Use ORM efficiently, avoid N+1 queries, use select_related/prefetch_related
1. **No commented code or removal comments** - Never leave comments about moved/removed code. We have git history for that.

## Permissions Guidelines

- **Allowed without asking**: Running tests, linting, code formatting, viewing files, reading API
- **Ask before**: Installing packages, making destructive operations, migrations
- **Never allowed**: Pushing directly to main branch, changing .env secrets

## Documentation

Detailed documentation is available in the `docs/` directory:

- **[Backend Conventions](docs/CONVENTIONS_BACKEND.md)** - Django/Python patterns, model conventions, API design, testing strategies, and database best practices

Refer to these documents when you need detailed information about specific aspects of the codebase.

## Essential Commands (Prioritized by Frequency)

### Most Used Commands

```bash
# Testing
pytest                          # Run all tests
pytest app/tests/test_*.py      # Run specific test file
pytest -k test_name             # Run specific test by name
pytest --cov=app                # Run with coverage report

# Linting & Formatting
black .                         # Format Python code
isort .                         # Sort imports
flake8                          # Check linting issues
pre-commit run                  # Run all pre-commit hooks
pre-commit run --all-files      # Run on entire codebase

# Development Server
python manage.py runserver      # Django server (port 8000)

# Django Shell
python manage.py shell_plus     # Interactive shell with models loaded
```

### Setup & Build Commands

```bash
# Initial Setup
poetry install                  # Install Python dependencies
poetry shell                    # Activate virtual environment
cp .env.example .env           # Create environment file
# Edit .env to set SECRET_KEY, DATABASE_URL, and REDIS_URL

# Database Operations
python manage.py migrate        # Run database migrations
python manage.py makemigrations # Create new migrations
python manage.py loaddata fixtures.json  # Load sample data
python manage.py createsuperuser         # Create admin user

# Data Management
python manage.py load_isa_data  # Import ISA data

# Docker Services
docker-compose up -d            # Start PostgreSQL and Redis
docker-compose down             # Stop services
docker-compose logs -f          # View logs
```

## Python Language Features

We use Python 3.10+. Take advantage of modern features:

- **Union syntax**: `str | None` instead of `Union[str, None]` or `Optional[str]`
- **F-strings**: Always prefer f-strings over `.format()` or `%` formatting
- **Type hints**: Use type hints for function arguments and return values where appropriate
- **Walrus operator**: `:=` for assignment expressions where it improves readability

## Workflow Decision Trees

### IF modifying Python files:

```
1. Check/write tests → pytest app/tests/test_*.py
2. Make code changes
3. Run tests → pytest
4. Format code → black . && isort .
5. Fix linting → flake8
6. Validate → pre-commit run
7. Commit atomically
```

### IF modifying models:

```
1. Update model in app/models.py
2. Create migration → python manage.py makemigrations
3. Review migration file
4. Apply migration → python manage.py migrate
5. Update tests
6. Run tests → pytest
7. Format & lint → black . && isort . && flake8
8. Commit atomically
```

### IF multiple unrelated changes exist:

```
1. Review all → git status && git diff
2. Reset staging → git reset
3. Group by type:
   - Features → git add <files> && git commit -m "feat: ..."
   - Fixes → git add <files> && git commit -m "fix: ..."
   - Tests → git add <files> && git commit -m "test: ..."
   - Docs → git add <files> && git commit -m "docs: ..."
```

## Quick Architecture Reference

For detailed architecture information, see [docs/CONVENTIONS_BACKEND.md](docs/CONVENTIONS_BACKEND.md).

**Key Points:**

- **Backend**: Django REST Framework API
- **Database**: PostgreSQL with UUID primary keys
- **Cache**: Redis for caching
- **Admin**: Customized Django admin with external links and computed fields
- **External Integration**: ISA (Instituto Socioambiental) data import

**Models Hierarchy:**

```
Country
├── State
│   └── Municipality
│       └── Land
└── Biome
    └── Land

Community ←→ Land (many-to-many)
```

**Land Categories:**

- **TI**: Terra Indígena
- **RI**: Reserva Indígena
- **PI**: Parque Indígena
- **DI**: Dominial Indígena

## Testing

For comprehensive testing guidelines, see [docs/CONVENTIONS_BACKEND.md](docs/CONVENTIONS_BACKEND.md).

**Key Requirements:**

- Tests must pass 100% - no exceptions
- Use pytest for Python tests
- Use factory-boy for test data creation
- Reuse database between test runs for performance (configured in pytest.ini)
- Use fixtures from `app/tests/conftest.py` if available

**Quick Examples:**

```python
# Using factories
from app.factories import LandFactory, CountryFactory

def test_land_creation():
    land = LandFactory(category="TI")
    assert land.category == "TI"

# Testing API endpoints
def test_land_list_api(client):
    LandFactory.create_batch(5)
    response = client.get('/api/lands/')
    assert response.status_code == 200
    assert len(response.json()) == 5
```

## Configuration

**Environment Variables** (`.env` file):

- `SECRET_KEY`: Django secret key (required)
- `DATABASE_URL`: PostgreSQL connection string (required)
- `REDIS_URL`: Redis connection string (required)
- `DEBUG`: Enable debug mode (default: False)

**Settings Module**: `config/settings.py` uses `django-environ` for environment-based configuration.

## Code Style & Conventions

For detailed coding standards, see [docs/CONVENTIONS_BACKEND.md](docs/CONVENTIONS_BACKEND.md).

**Quick Reference:**

- **Max line length**: 120 characters
- **Import order**: stdlib → django → third-party → local (enforced by isort)
- **Excluded from linting**: migrations, static, docs, node_modules, venv

## Django Admin Customization

The admin interface (`app/admin.py`) includes:

- Custom list displays with computed fields
- External link generation for ISA data
- Search and filter capabilities
- Autocomplete fields for many-to-many relationships

## API Design

**URL Structure:**

- `/api/countries/` - Country list and detail
- `/api/states/` - State list and detail
- `/api/municipalities/` - Municipality list and detail
- `/api/biomes/` - Biome list and detail
- `/api/lands/` - Land list and detail with filtering
- `/api/communities/` - Community list and detail
- `/admin/` - Django admin interface
- `/api/schema/` - OpenAPI schema (drf-spectacular)

**API Features:**

- Filtering via django-filter
- OpenAPI documentation via drf-spectacular
- Nested serializers for related objects
- Separate read/write fields for foreign keys

## Common Tasks

### Adding a New Model Field

```bash
# 1. Add field to model
# 2. Create migration
python manage.py makemigrations

# 3. Review the migration file
# 4. Apply migration
python manage.py migrate

# 5. Update serializer if exposing via API
# 6. Update tests
# 7. Run tests
pytest
```

### Loading External Data

```bash
# Import ISA data
python manage.py load_isa_data

# Load fixtures
python manage.py loaddata fixtures.json
```

### Running Code Quality Checks

```bash
# Format code
black .
isort .

# Check for issues
flake8

# Run all pre-commit hooks
pre-commit run --all-files
```

## DO NOT (Common Mistakes)

- **DO NOT use `/tmp`** → Use `tmp/` instead (permission issues)
- **DO NOT git push** → Leave this decision to the human
- **DO NOT combine commits** → One feature/fix per commit
- **DO NOT skip tests** → All tests must pass
- **DO NOT skip pre-commit** → Always run before committing
- **DO NOT expose all model fields** → Be explicit about API fields in serializers
- **DO NOT create N+1 queries** → Use select_related/prefetch_related
- **DO NOT use naive datetimes** → Always use timezone-aware datetimes

## Git Commit Guidelines

**Format**: `<type>: <what changed>` (under 72 chars, present tense)

**Types**: `feat|fix|docs|refactor|test|chore`

**Examples:**

```bash
feat: add Community model with many-to-many relationship
fix: correct ISA link generation for lands
test: add tests for land filtering by category
docs: update API documentation for biome endpoints
refactor: optimize land queryset with select_related
chore: update dependencies to latest versions
```

### Multiple Changes Example

```bash
# Review changes
git status && git diff

# Reset and commit atomically
git reset

# Commit feature
git add app/models.py app/migrations/
git commit -m "feat: add municipality field to Land model"

# Commit API changes
git add app/serializers.py app/viewsets.py
git commit -m "feat: expose municipality in Land API"

# Commit tests
git add app/tests/
git commit -m "test: add municipality filtering tests"
```

## Additional Notes

- Check for deprecation warnings when running tests
- Use type hints where appropriate
- Follow existing code patterns in the codebase
- When in doubt, check how similar functionality is implemented
- Consult detailed documentation in `docs/` for specific topics
- Use Django's ORM efficiently (select_related, prefetch_related, bulk operations)
- Always use timezone-aware datetimes via `django.utils.timezone`
