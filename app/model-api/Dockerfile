# ----------- Build Stage -------------
FROM python:3.9-slim AS builder

# Copy uv binary into the image (from published container)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Environment variables
ENV UV_BREAK_SYSTEM_PACKAGES=true \
    UV_SYSTEM_PYTHON=true

# Set working directory
WORKDIR /app

# Create virtual environment
RUN python -m venv /opt/venv && \
    cp /bin/uv /opt/venv/bin/uv

# Copy only requirements first (leverage Docker cache)
COPY requirements.txt .

# Install all Python dependencies using pip inside venv
RUN /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# ----------- Final Stage -------------
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    PORT=5000 \
    HOST=0.0.0.0

# Install system packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    curl \
    libopenblas-dev \
    liblapack-dev \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Copy virtual environment
COPY --from=builder /opt/venv /opt/venv

# Copy your app code
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Expose FastAPI port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=60s --timeout=30s --start-period=90s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Run FastAPI
CMD ["/opt/venv/bin/uvicorn", "main:app", "--host=0.0.0.0", "--port=5000"]
