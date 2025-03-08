FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements.txt first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create a non-root user and switch to it for security
RUN useradd -m appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "backend.api:app", "--host", "0.0.0.0", "--port", "8000"] 