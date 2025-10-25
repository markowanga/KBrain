#!/bin/bash
set -e

echo "=========================================="
echo "KBrain Backend - Service Startup"
echo "=========================================="

# Navigate to backend directory
cd /app

# Run database migrations
echo ""
echo "Running database migrations..."
cd services/kbrain-backend
uv run alembic upgrade head

# Show current database version
echo ""
echo "Current database version:"
uv run alembic current

# Start the FastAPI application
echo ""
echo "=========================================="
echo "Starting FastAPI server..."
echo "=========================================="
cd /app
uv run fastapi run services/kbrain-backend/src/kbrain_backend/main.py