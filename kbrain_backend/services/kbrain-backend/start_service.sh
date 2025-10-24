#!/bin/bash
set -e

# Start the FastAPI application
echo "Starting FastAPI server..."
cd /app
uv run fastapi run services/kbrain-backend/src/kbrain_backend/main.py