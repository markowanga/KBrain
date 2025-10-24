FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

WORKDIR /app

# Copy the project files
COPY pyproject.toml .
COPY services services
COPY libs libs

# Install dependencies
RUN uv sync --all-packages

# Expose the port
EXPOSE 8000
RUN chmod +x /app/services/kbrain-backend/start_service.sh
# Run the application
ENTRYPOINT ["./services/kbrain-backend/start_service.sh"]
