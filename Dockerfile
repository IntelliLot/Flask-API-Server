# Dockerfile for YOLOv8 Parking Detection System
# Multi-stage build for optimized production image

FROM python:3.10-slim as base

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements_full.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements_full.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p output uploads

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app.py

# Expose port (will be overridden in docker-compose)
EXPOSE 5001

# Default command (will be overridden in docker-compose)
CMD ["python", "app.py"]
