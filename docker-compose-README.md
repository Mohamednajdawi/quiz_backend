# Docker Compose Configuration for Quiz Application

## Overview
This document explains how to use Docker Compose to run the Quiz application with persistent database storage.

## Prerequisites
- Docker and Docker Compose installed on your system
- Basic knowledge of Docker commands

## Getting Started

1. **Build and start the application:**
   ```bash
   docker-compose up -d
   ```
   This command will build the Docker image and start the service in detached mode.

2. **Accessing the application:**
   The application will be available at http://localhost:8000

3. **Viewing logs:**
   ```bash
   docker-compose logs -f
   ```

4. **Stopping the application:**
   ```bash
   docker-compose down
   ```

## Database Persistence

The quiz database is stored in a volume that is mapped to the local file `quiz_database.db`. 
This ensures:
- All quiz data is persistent across container restarts
- New quizzes generated in the container are automatically saved to your local database file
- The database can be backed up simply by copying the local file

## Troubleshooting

If you encounter any issues:
1. Check the logs with `docker-compose logs -f`
2. Ensure your database file permissions allow read/write from the container
3. Rebuild with `docker-compose build --no-cache` if code changes aren't reflected 