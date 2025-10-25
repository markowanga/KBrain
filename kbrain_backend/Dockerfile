FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

WORKDIR /app

# Copy the project files
COPY pyproject.toml .
COPY services services
COPY libs libs

# Install dependencies
RUN uv sync --all-packages

# Add virtual environment to PATH so Python is available globally
ENV PATH="/app/.venv/bin:$PATH"

# Make the virtual environment the default Python
ENV VIRTUAL_ENV="/app/.venv"

# Set script as executable
RUN chmod +x /app/services/kbrain-backend/start_service.sh

# Expose the port
EXPOSE 8000

# Run the application
ENTRYPOINT ["./services/kbrain-backend/start_service.sh"]
