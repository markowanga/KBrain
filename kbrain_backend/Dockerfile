FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

WORKDIR /app

# Copy the project files
COPY pyproject.toml .
COPY main.py .

# Install dependencies
RUN uv pip install --system -r pyproject.toml

# Expose the port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
