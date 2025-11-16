# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Monguite is a Django web application for managing and tracking indigenous land data, including countries, states, municipalities, biomes, communities, and land categories. The project focuses on Brazilian indigenous territories with integration to external data sources (ISA - Instituto Socioambiental). The application provides both a Django admin interface and a RESTful API with Model Context Protocol (MCP) server integration for AI assistants.

## Development Setup

**Dependencies**: This project uses Poetry for dependency management.

```bash
# Install dependencies (includes dev dependencies)
poetry install

# Activate virtual environment
poetry shell

# Copy environment file and configure
cp .env.example .env
# Edit .env to set SECRET_KEY, DATABASE_URL, and REDIS_URL
```

**Database**: PostgreSQL is required. Redis is used for caching.

```bash
# Start database services (using Docker Compose)
docker compose up -d

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

# API will be available at:
# - http://localhost:8000/api/v1/
# - http://localhost:8000/api/v1/docs/ (Swagger UI)
# - http://localhost:8000/api/v1/redoc/ (ReDoc)
```

**Testing**:
```bash
# Run all tests
pytest

# Run specific test file
pytest app/tests/test_views.py
pytest app/tests/test_commands.py
pytest app/test_api.py

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

**Data import**:
```bash
# Import indigenous land data from ISA
python manage.py load_isa_data

# Import from local JSON file
python manage.py load_isa_data path/to/data.json

# Dry run (test without saving)
python manage.py load_isa_data --dry-run

# Update existing records
python manage.py load_isa_data --update
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

**MCP Server** (for AI assistants):
```bash
# Set environment variables
export MONGUITE_API_URL="http://localhost:8000"
export MONGUITE_API_TOKEN=""  # Optional

# Run MCP server
python mcp/server.py
```

## Project Structure

**Settings module**: `config/settings.py` - Django settings are in the `config` directory, not a typical project-named directory. The settings module uses `django-environ` for environment-based configuration.

**Main app**: `app/` - Single Django app containing all models, views, serializers, viewsets, filters, and admin configuration.

**MCP server**: `mcp/` - Model Context Protocol server for AI assistant integration.

### Models Hierarchy

All models use UUID as primary keys for better external integration and data synchronization.

- `Country` - Top-level geographic entity with name and ISO codes
  - Fields: `id` (UUID), `name`, `code` (2-char ISO)

- `State` - Administrative divisions (estados)
  - Fields: `id` (UUID), `name`, `name_local`, `code`, `country` (FK)
  - Belongs to: Country

- `Municipality` - Cities/municipalities (municípios)
  - Fields: `id` (UUID), `name`, `name_local`, `code`, `state` (FK)
  - Belongs to: State
  - New in recent version

- `Biome` - Ecological regions with area tracking
  - Fields: `id` (UUID), `name`, `name_local`, `description`, `description_local`, `country` (FK)
  - Belongs to: Country

- `Community` - Indigenous communities (povos indígenas)
  - Fields: `id` (UUID), `name`, `slug`
  - Auto-generates slug from name
  - New in recent version

- `Land` - Indigenous territories with category classification
  - Fields: `id` (UUID), `name`, `category`, `municipality` (FK), `biome` (FK), `communities` (M2M)
  - Source integration fields: `source_id`, `source_name`, `source_updated_at`, `source_last_synced_at`, `source_raw_data`
  - Unique constraint: `(source_name, source_id)`
  - Belongs to: Municipality (nullable), Biome (nullable)
  - Related to: Communities (many-to-many)

### Admin Customization

The Django admin (`app/admin.py`) has significant customization:
- `BiomeAdmin` - Shows calculated preservation rates and related lands count
- `LandAdmin` - Includes external ISA link generation for lands with `source_id`

### URL Structure

- Root URLs in `config/urls.py`
- App-specific URLs in `app/urls.py`
- Admin at `/admin/`
- Debug toolbar at `/__debug__/` (development only)
- **REST API at `/api/v1/`** (new):
  - `/api/v1/lands/` - List and retrieve lands (read-only)
  - `/api/v1/communities/` - List and retrieve communities (read-only)
  - `/api/v1/schema/` - OpenAPI schema
  - `/api/v1/docs/` - Swagger UI documentation
  - `/api/v1/redoc/` - ReDoc documentation

### API Implementation

**Viewsets** (`app/viewsets.py`):
- `LandViewSet` - Read-only viewset with comprehensive filtering and annotations
- `CommunityViewSet` - Read-only viewset with lands count annotation

**Serializers** (`app/serializers.py`):
- Nested serializers for related models (Country, State, Municipality, Biome)
- `LandSerializer` - Includes flattened location info and source links
- `CommunitySerializer` - Includes computed lands count

**Filters** (`app/filters.py`):
- `LandFilter` - Filter by name, category, location (municipality, state, country), biome, community, and counts
- `CommunityFilter` - Filter by name and lands count ranges

**Features**:
- Pagination enabled
- Full-text search support
- Ordering/sorting capabilities
- Optimized queries with select_related and prefetch_related
- Query annotations for better performance (avoid N+1 queries)
- OpenAPI schema generation via drf-spectacular

## Key Technical Details

**Database**: The project uses PostgreSQL with atomic requests enabled (`ATOMIC_REQUESTS = True`). Each request is wrapped in a transaction.

**Caching**: Redis cache configured with `django_redis` backend. Exception handling mimics memcache behavior (ignores exceptions).

**Primary Keys**: All models use UUID primary keys (UUIDField with uuid4 default) for better data synchronization and external integration.

**External Integration**:
- Land model contains source integration fields for tracking external data sources
- ISA (Instituto Socioambiental) integration via `load_isa_data` management command
- Source link generation in serializers (e.g., `https://terrasindigenas.org.br/en/terras-indigenas/{source_id}`)

**Land Categories**: Four indigenous land categories defined in `Land.CATEGORY_CHOICES`:
- `DI`: Dominial Indígena
- `PI`: Parque Indígena
- `RI`: Reserva Indígena
- `TI`: Terra Indígena

## MCP Server Integration

The project includes a Model Context Protocol (MCP) server (`mcp/server.py`) for AI assistant integration.

**Available Tools**:
1. `search_lands` - Search lands with filters (name, category, location, biome, community)
2. `get_land_details` - Get detailed information about a specific land by UUID
3. `search_communities` - Search communities with filters (name, lands count)
4. `get_community_details` - Get detailed information about a community by UUID
5. `get_api_stats` - Get summary statistics (total lands, total communities)

**Configuration**:
- `MONGUITE_API_URL` - Base URL for the API (default: `http://localhost:8000`)
- `MONGUITE_API_TOKEN` - Optional authentication token

**Running the MCP server**:
```bash
# In Claude Desktop config (~/.config/Claude/claude_desktop_config.json):
{
  "mcpServers": {
    "monguite": {
      "command": "python",
      "args": ["/path/to/monguite/mcp/server.py"],
      "env": {
        "MONGUITE_API_URL": "http://localhost:8000",
        "MONGUITE_API_TOKEN": ""
      }
    }
  }
}
```

## Data Import

**ISA Data Import Command** (`app/management/commands/load_isa_data.py`):

This command imports indigenous land data from ISA (Instituto Socioambiental).

```bash
# Download and import from ISA URL (default)
python manage.py load_isa_data

# Import from local file
python manage.py load_isa_data data.json

# Test without saving (dry run)
python manage.py load_isa_data --dry-run

# Update existing records
python manage.py load_isa_data --update
```

**Data Transformation**:
- Downloads from `https://mapa.eco.br/data/sisarp/v1/tis.json` by default
- Creates/updates Land, Municipality, State, Community records
- Handles multiple JSON formats (wrapped and direct array)
- Stores complete raw JSON in `source_raw_data` field
- Automatic timestamp tracking for syncs and updates

**Important Notes**:
- Creates Brazil country automatically if it doesn't exist
- Municipalities are created with state relationships
- Communities are deduplicated by name and slug
- Use `--dry-run` to preview changes before committing
- Use `--update` to update existing records (skips by default)

## Code Standards

**Linting Configuration** (setup.cfg):
- Max line length: 120 characters
- Excludes: migrations, static cache, docs, node_modules, venv

**Pre-commit Hooks** (`.pre-commit-config.yaml`):
Configured to run on push (not commit). Includes:
- `black` - Code formatting (line length: 120)
- `isort` - Import sorting
- `flake8` - Linting with isort integration
- Standard pre-commit hooks:
  - Trailing whitespace removal
  - End-of-file fixer
  - YAML/JSON syntax checking
  - Debug statement detection
  - Private key detection
  - Large file detection

**Testing**:
- pytest-django is configured to use `config.settings`
- Database reuse enabled for performance (`--reuse-db`)
- Test organization:
  - `app/tests/test_views.py` - View tests
  - `app/tests/test_commands.py` - Management command tests
  - `app/test_api.py` - API endpoint tests

## Development Workflow

**Adding New Features**:
1. Update models in `app/models.py`
2. Create migrations: `python manage.py makemigrations`
3. Apply migrations: `python manage.py migrate`
4. Update serializers if API changes needed
5. Update filters for new query capabilities
6. Add tests for new functionality
7. Update admin interface if needed
8. Run code quality checks: `black . && isort . && flake8`
9. Run tests: `pytest`

**API Development**:
- Use viewsets for consistent API design
- Add filters in `app/filters.py` using django-filter
- Use annotations in querysets for performance
- Document with drf-spectacular decorators
- Test all endpoints in `app/test_api.py`

**Common Patterns**:
- Use `select_related()` for foreign key relationships
- Use `prefetch_related()` for many-to-many relationships
- Use `annotate()` for computed fields to avoid N+1 queries
- Use `F()` expressions for database-level field references
- Keep transactions atomic (already enabled globally)

## Dependencies

**Core**:
- Django 5.1
- psycopg2-binary (PostgreSQL adapter)
- django-environ (environment configuration)
- django-redis (Redis cache backend)
- requests (HTTP library)

**API**:
- djangorestframework 3.16+
- django-filter 25.2+
- drf-spectacular 0.29+ (OpenAPI/Swagger)

**MCP** (optional group):
- mcp 0.9+
- httpx 0.27+
- pydantic 2.0+

**Development**:
- pytest-django
- factory-boy (test fixtures)
- coverage
- black (formatting)
- isort (import sorting)
- flake8 (linting)
- pre-commit
- django-debug-toolbar
- django-extensions

**Installation**:
```bash
# All dependencies including dev
poetry install

# Production only
poetry install --only main

# With MCP support
poetry install --with mcp
```

## Troubleshooting

**Database Connection Issues**:
- Check DATABASE_URL in .env file
- Ensure PostgreSQL is running: `docker compose ps`
- Check credentials match docker-compose.yml

**Redis Connection Issues**:
- Check REDIS_URL in .env file
- Ensure Redis is running: `docker compose ps`
- Redis failures are gracefully handled (ignored)

**Migration Conflicts**:
- Reset database: `docker compose down -v && docker compose up -d`
- Rerun migrations: `python manage.py migrate`

**Import Errors**:
- Ensure virtual environment is activated: `poetry shell`
- Reinstall dependencies: `poetry install`

**API 404 Errors**:
- Check URL patterns in `config/urls.py`
- Verify router registration in config/urls.py
- Ensure API prefix is `/api/v1/`

## Additional Resources

- Django documentation: https://docs.djangoproject.com/
- Django REST Framework: https://www.django-rest-framework.org/
- drf-spectacular: https://drf-spectacular.readthedocs.io/
- MCP specification: https://modelcontextprotocol.io/
- ISA data source: https://terrasindigenas.org.br/
