# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Django REST Framework project configured to run on **Uvicorn** (ASGI server) demonstrating various async/sync patterns for handling concurrent operations in Django. The project showcases different approaches to concurrency including ThreadPoolExecutor, asyncio, and Django's async views.

## Development Commands

### Running the Server
```bash
uvicorn core.asgi:application --reload
```

### Database Operations
```bash
# Run migrations
python manage.py migrate

# Create migrations after model changes
python manage.py makemigrations

# Create superuser for admin access
python manage.py createsuperuser
```

### Dependency Management
This project uses **Poetry** for dependency management:
```bash
# Install dependencies
poetry install

# Add a new dependency
poetry add <package-name>

# Update dependencies
poetry update
```

## Architecture

### Project Structure
- **core/**: Django project configuration
  - `settings.py`: Project settings (SQLite, REST Framework config)
  - `asgi.py`: ASGI application entry point for Uvicorn
  - `urls.py`: Root URL configuration

- **persons/**: Django app demonstrating async patterns
  - `models.py`: Person model (name, age)
  - `api/`: API implementation with versioning
    - `v1/`: Version 1 of the API
      - `views.py`: ViewSets and APIViews with sync/async examples
      - `serializers.py`: DRF serializers
      - `urls.py`: API endpoint routing

### URL Routing Pattern
The project uses a nested URL structure:
```
/ → persons.urls → persons.api.urls → persons.api.v1.urls
```

Final API endpoints are mounted at: `/api/v1/`

### API Endpoints
- `/api/v1/persons/` - Standard DRF ModelViewSet (CRUD operations)
- `/api/v1/check/` - Sync view using ThreadPoolExecutor
- `/api/v1/create_bulk/` - Sync view with ThreadPoolExecutor decorator
- `/api/v1/async_create_bulk/` - Async view using sync_to_async
- `/api/v1/fetch_data/` - Async view with aiohttp and asyncio.gather

### Key Patterns Demonstrated

**1. ThreadPoolExecutor Pattern (CheckPersonAPIView)**
- Uses concurrent.futures.ThreadPoolExecutor for offloading blocking operations
- Wraps synchronous Django ORM calls in executor.submit()

**2. Custom Thread Pool Decorator (CreatePersonAPIView)**
- Reusable `@thread_pool` decorator that wraps any function
- Automatically handles ThreadPoolExecutor context

**3. Async with sync_to_async (AsyncCreatePersonAPIView)**
- Uses Django's `@sync_to_async` decorator to wrap ORM operations
- Integrates with asyncio.gather for concurrent task execution
- Suitable for mixing Django ORM with async code

**4. Pure Async with aiohttp (AsyncFetchDataAPIView)**
- Fully async implementation using aiohttp.ClientSession
- Uses asyncio.gather for concurrent HTTP requests
- Demonstrates async/await pattern with external API calls

### Important Technical Details

- **ASGI Configuration**: The project uses `ASGI_APPLICATION = 'core.asgi.application'` in settings
- **REST Framework**: Configured with JSONRenderer only (no browsable API)
- **Logging**: Uses loguru for structured logging throughout async views
- **Database**: SQLite with standard Django ORM (no async ORM support)
- **Dependencies**: channels library is installed for ASGI support

## Development Guidelines

### When Adding New Endpoints
1. Follow the established API versioning pattern under `persons/api/v1/`
2. Choose appropriate concurrency pattern based on operation type:
   - Use ThreadPoolExecutor for CPU-bound Django ORM operations
   - Use async views with sync_to_async for mixed sync/async operations
   - Use pure async with aiohttp for external API calls
   - Use standard DRF views for simple CRUD operations

### Working with Async Code
- Django ORM operations are synchronous - wrap with `@sync_to_async` when using in async views
- Use `asyncio.gather()` for concurrent task execution with proper error handling
- Always use async context managers (e.g., `async with aiohttp.ClientSession()`)

### Database Migrations
After modifying models in `persons/models.py`, always:
1. Create migrations: `python manage.py makemigrations`
2. Apply migrations: `python manage.py migrate`
