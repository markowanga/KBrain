# KBrain Backend API

Knowledge Management System Backend API built with FastAPI.

## Features

- RESTful API for document and scope management
- Multiple storage backends (Local, S3, Azure Blob)
- PostgreSQL database with SQLAlchemy ORM
- Async/await support for high performance
- Comprehensive API documentation with OpenAPI/Swagger
- Error handling and validation

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- uv (Python package manager)

### Installation

1. Install dependencies:
```bash
uv sync
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Set up database:
```bash
# Create PostgreSQL database
createdb kbrain

# The tables will be created automatically on first run
```

4. Run the server:
```bash
uv run uvicorn main:app --reload
```

The API will be available at http://localhost:8000

## API Documentation

Once the server is running, you can access:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/v1/openapi.json
