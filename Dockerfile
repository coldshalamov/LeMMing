# LeMMing Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -e ".[api,llm]"

# Create data directory for agents
RUN mkdir -p /data/agents

# Environment variables
ENV OPENAI_API_KEY=""
ENV ANTHROPIC_API_KEY=""
ENV PYTHONUNBUFFERED=1

# Expose API port
EXPOSE 8000

# Default command: run API server
CMD ["python", "-m", "lemming.cli", "serve", "--host", "0.0.0.0", "--port", "8000"]
