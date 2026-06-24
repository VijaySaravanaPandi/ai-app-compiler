# Dockerfile
# =========
# Multi-stage image build for python FastAPI server and Node.js runtime

FROM python:3.11-slim

# Install system dependencies & Node.js for execution awareness
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set up working directory structure
WORKDIR /app

# Copy requirements and install dependencies first (for docker caching)
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy source folders
COPY backend /app/backend
COPY frontend /app/frontend

# Create directory to store compiled zip files & sqlite databases
RUN mkdir -p /app/generated_apps /app/backend/generated_apps

# Expose backend port
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Run uvicorn from the backend/ directory so app module imports resolve correctly
WORKDIR /app/backend
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
