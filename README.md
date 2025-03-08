# Quiz API Backend

This repository contains a FastAPI-based backend for a quiz application.

## Requirements

- Python 3.11+
- Dependencies listed in `pyproject.toml`

## Local Development Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -e .
   ```
3. Run the FastAPI application:
   ```bash
   uvicorn backend.api:app --reload
   ```

## Docker Setup

The project includes a Docker configuration for easy deployment and consistent environments.

### Building the Docker Image

```bash
docker build -t quiz-backend .
```

### Running the Docker Container

```bash
docker run -p 8000:8000 quiz-backend
```

This exposes the FastAPI application on port 8000. You can access:
- API endpoints at `http://localhost:8000/`
- Interactive API documentation at `http://localhost:8000/docs`

### Docker Configuration Details

The Dockerfile:
- Uses Python 3.11 slim as the base image
- Installs necessary system dependencies
- Optimizes caching of Python dependencies
- Runs the application as a non-root user for better security
- Exposes port 8000 for the FastAPI application

## API Documentation

When the application is running, visit `http://localhost:8000/docs` to view the interactive API documentation.
