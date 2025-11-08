# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Django REST Framework project configured to run on **Uvicorn** (ASGI server) demonstrating various async/sync patterns for handling concurrent operations in Django. The project showcases different approaches to concurrency including ThreadPoolExecutor, asyncio, and Django's async views with production-ready features including error handling, validation, pagination, and security.

## Development Commands

### Initial Setup
```bash
# Install dependencies using Poetry
poetry install

# Copy .env.example to .env and configure your environment
cp .env.example .env

# Run migrations
python manage.py migrate

# Create superuser for admin access (optional)
python manage.py createsuperuser
```

### Running the Server
```bash
# Development mode with auto-reload
uvicorn core.asgi:application --reload

# Production mode
uvicorn core.asgi:application --host 0.0.0.0 --port 8000
```

### Testing
```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=persons

# Run specific test file
pytest persons/tests.py

# Run tests in verbose mode
pytest -v
```

### Database Operations
```bash
# Run migrations
python manage.py migrate

# Create migrations after model changes
python manage.py makemigrations

# Show migrations
python manage.py showmigrations
```

### Dependency Management
This project uses **Poetry** for dependency management:
```bash
# Install dependencies
poetry install

# Add a new dependency
poetry add <package-name>

# Add a dev dependency
poetry add --group dev <package-name>

# Update dependencies
poetry update

# Show installed packages
poetry show
```

## Architecture

### Project Structure
- **core/**: Django project configuration
  - `settings.py`: Project settings with environment variable support, CORS, pagination
  - `asgi.py`: ASGI application entry point for Uvicorn
  - `urls.py`: Root URL configuration

- **persons/**: Django app demonstrating async patterns
  - `models.py`: Person model (name, age)
  - `tests.py`: Comprehensive test suite
  - `api/`: API implementation with versioning
    - `v1/`: Version 1 of the API
      - `views.py`: ViewSets and APIViews with sync/async examples, error handling, validation
      - `serializers.py`: DRF serializers
      - `urls.py`: API endpoint routing

### URL Routing Pattern
The project uses a nested URL structure:
```
/ → persons.urls → persons.api.urls → persons.api.v1.urls
```

Final API endpoints are mounted at: `/api/v1/`

### API Endpoints

**Standard CRUD**
- `GET /api/v1/persons/` - List all persons (paginated)
- `POST /api/v1/persons/` - Create a new person
- `GET /api/v1/persons/{id}/` - Retrieve a person
- `PUT /api/v1/persons/{id}/` - Update a person
- `DELETE /api/v1/persons/{id}/` - Delete a person

**Async/Sync Demonstration Endpoints**
- `GET /api/v1/check/?pk=<id>` - Sync view using ThreadPoolExecutor with error handling
- `POST /api/v1/create_bulk/` - Sync view with ThreadPoolExecutor decorator (JSON body: `{"count": <number>}`)
- `POST /api/v1/async_create_bulk/` - Async view using sync_to_async with bulk_create (JSON body: `{"count": <number>}`)
- `GET /api/v1/fetch_data/` - Pure async view with aiohttp for concurrent HTTP requests

### Key Patterns Demonstrated

**1. ThreadPoolExecutor Pattern (CheckPersonAPIView)**
- Uses concurrent.futures.ThreadPoolExecutor for offloading blocking operations
- Wraps synchronous Django ORM calls in executor.submit()
- Includes comprehensive error handling and validation
- Returns 404 for missing records, 400 for invalid input

**2. Custom Thread Pool Decorator (CreatePersonAPIView)**
- Reusable `@thread_pool` decorator that wraps any function
- Automatically handles ThreadPoolExecutor context
- **Changed from GET to POST** for proper REST semantics
- Validates input count (1-10000 limit)
- Includes rate limiting via reduced sleep time

**3. Async with sync_to_async (AsyncCreatePersonAPIView)**
- Uses Django's `@sync_to_async` decorator to wrap ORM operations
- **Uses bulk_create** for efficient database operations (500 batch size)
- Integrates with asyncio.gather for concurrent task execution
- Validates JSON input with proper error messages
- Suitable for mixing Django ORM with async code

**4. Pure Async with aiohttp (AsyncFetchDataAPIView)**
- Fully async implementation using aiohttp.ClientSession
- Uses asyncio.gather for concurrent HTTP requests
- Demonstrates async/await pattern with external API calls
- Includes timeout handling (10s per request)
- Graceful error handling with descriptive error objects

### Important Technical Details

**Security & Configuration**
- **Environment Variables**: Uses python-dotenv for configuration management
- **SECRET_KEY**: Loaded from .env file (NEVER commit actual secrets)
- **DEBUG**: Controlled via environment variable (default: False for safety)
- **ALLOWED_HOSTS**: Configurable via environment variable
- **CORS**: django-cors-headers configured with environment-based origins

**API Features**
- **Pagination**: Enabled globally (100 items per page)
- **Error Handling**: All views include try-catch with appropriate HTTP status codes
- **Validation**: Input validation on all endpoints (type checking, range limits)
- **Logging**: Structured logging with loguru (info, debug, error levels)

**Database & ORM**
- **Database**: SQLite for development (consider PostgreSQL for production)
- **ASGI Application**: `ASGI_APPLICATION = 'core.asgi.application'`
- **Bulk Operations**: Uses bulk_create for efficient inserts
- **Async ORM**: Django ORM is sync - always wrap with @sync_to_async

**Testing**
- **Framework**: pytest with pytest-django and pytest-asyncio
- **Coverage**: Tests for models, API endpoints, async views
- **Configuration**: pytest.ini with Django settings and asyncio mode

## Development Guidelines

### Environment Variables
Always use environment variables for sensitive data:
1. Copy `.env.example` to `.env`
2. Update values for your environment
3. Never commit `.env` to version control
4. In production, use proper secret management

### When Adding New Endpoints
1. Follow the established API versioning pattern under `persons/api/v1/`
2. Choose appropriate concurrency pattern based on operation type:
   - Use ThreadPoolExecutor for CPU-bound Django ORM operations
   - Use async views with sync_to_async for mixed sync/async operations
   - Use pure async with aiohttp for external API calls
   - Use standard DRF views for simple CRUD operations
3. Always include error handling and input validation
4. Use appropriate HTTP methods (GET for read, POST for create, etc.)
5. Add logging statements for debugging and monitoring
6. Write tests for new functionality

### Working with Async Code
- Django ORM operations are synchronous - wrap with `@sync_to_async` when using in async views
- Use `asyncio.gather()` for concurrent task execution with `return_exceptions=True`
- Always use async context managers (e.g., `async with aiohttp.ClientSession()`)
- Set timeouts for external HTTP requests to prevent hanging
- For bulk database operations, use `bulk_create()` with appropriate batch_size
- Handle exceptions gracefully with descriptive error messages

### Security Best Practices
- Never hardcode secrets in code
- Use environment variables for configuration
- Set DEBUG=False in production
- Validate all user input
- Implement rate limiting for bulk operations
- Use HTTPS in production
- Keep dependencies updated

### Testing Guidelines
- Write tests for all new endpoints and models
- Test both success and error cases
- Use pytest markers (@pytest.mark.django_db, @pytest.mark.asyncio)
- Test validation and error handling
- Run tests before committing changes

### Database Migrations
After modifying models in `persons/models.py`, always:
1. Create migrations: `python manage.py makemigrations`
2. Review migrations: Check the generated migration file
3. Apply migrations: `python manage.py migrate`
4. Test migrations: Ensure data integrity is maintained

### Performance Optimization
- Use bulk_create() for creating multiple objects
- Add database indexes for frequently queried fields
- Use select_related() and prefetch_related() for complex queries
- Consider caching for read-heavy endpoints
- Monitor query performance with Django Debug Toolbar (dev only)
- For production, use PostgreSQL instead of SQLite for better concurrency
