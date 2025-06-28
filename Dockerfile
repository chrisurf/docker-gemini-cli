# Use official Python slim image as base
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create non-root user for security
RUN groupadd -r gemini && useradd -r -g gemini gemini

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    jq \
    nano \
    vim \
    wget \
    unzip \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create application directories
RUN mkdir -p /app/data /app/logs /app/config /app/scripts && \
    chown -R gemini:gemini /app

# Set working directory
WORKDIR /app

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Google Generative AI CLI (gemini-cli)
RUN pip install --no-cache-dir google-generativeai

# Copy application files
COPY --chown=gemini:gemini src/ ./src/
COPY --chown=gemini:gemini config/ ./config/
COPY --chown=gemini:gemini scripts/ ./scripts/
COPY --chown=gemini:gemini entrypoint.sh .

# Make scripts executable
RUN chmod +x entrypoint.sh scripts/*.sh

# Create volume mount points
VOLUME ["/app/data", "/app/logs"]

# Switch to non-root user
USER gemini

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python src/health_check.py

# Expose port for optional web interface
EXPOSE 8080

# Set entrypoint
ENTRYPOINT ["./entrypoint.sh"]

# Default command
CMD ["agent"]