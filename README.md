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

## Heroku Deployment

Follow these steps to deploy the application to Heroku:

### Prerequisites

1. Install the [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli)
2. Login to Heroku:
   ```bash
   heroku login
   ```

### Deployment Steps

1. Create a Heroku app:
   ```bash
   heroku create quiz-maker-api
   ```

2. Add a PostgreSQL database:
   ```bash
   heroku addons:create heroku-postgresql:essential-0 --app quiz-maker-api
   ```

3. Set up environment variables:
   ```bash
   heroku config:set GROQ_API_KEY=your_groq_api_key --app quiz-maker-api
   ```

4. Initialize a Git repository (if not already done):
   ```bash
   git init
   git add .
   git commit -m "Initial commit for Heroku deployment"
   ```

5. Add Heroku as a remote and set it to use container-based deployment:
   ```bash
   heroku git:remote -a quiz-maker-api
   heroku stack:set container --app quiz-maker-api
   ```

6. Push the code to Heroku:
   ```bash
   git push heroku main
   ```

7. Initialize the database:
   ```bash
   heroku run python init_db.py --app quiz-maker-api
   ```

8. Open the application:
   ```bash
   heroku open --app quiz-maker-api
   ```

### Starting and Stopping the App

To stop the application (e.g., to save on dyno hours): *this one*
```bash
heroku ps:scale web=0 --app quiz-maker-api
```

To start the application again: *this one*
```bash
heroku ps:scale web=1 --app quiz-maker-api
```

You can also put the app in maintenance mode (which shows a maintenance page to users):
```bash
# Enable maintenance mode
heroku maintenance:on --app quiz-maker-api

# Disable maintenance mode
heroku maintenance:off --app quiz-maker-api
```

### Managing Heroku Postgres Add-on

#### Viewing Database Information
```bash
# List all add-ons including Postgres
heroku addons --app quiz-maker-api

# Get detailed information about your Postgres database
heroku pg:info --app quiz-maker-api
```

#### Managing Postgres Costs
Heroku doesn't provide a direct way to pause PostgreSQL databases. To manage costs when not using the database for extended periods:

1. Create a backup of your database:
   ```bash
   # Create a backup
   heroku pg:backups:capture --app quiz-maker-api
   
   # Download the backup (optional)
   heroku pg:backups:download --app quiz-maker-api
   ```

2. Remove the Postgres add-on:
   ```bash
   heroku addons:destroy postgresql --app quiz-maker-api --confirm quiz-maker-api
   ```

3. When needed again, recreate the database:
   ```bash
   # Create a new Postgres database
   heroku addons:create heroku-postgresql:essential-0 --app quiz-maker-api
   
   # Initialize the database tables
   heroku run python init_db.py --app quiz-maker-api
   ```

4. Restore from backup (if needed):
   ```bash
   # If you have a backup URL
   heroku pg:backups:restore [BACKUP_URL] --app quiz-maker-api
   
   # Or restore from the latest backup
   heroku pg:backups:restore --app quiz-maker-api
   ```

### Important Files for Heroku Deployment

- `requirements.txt`: Lists all Python dependencies
- `Procfile`: Tells Heroku how to run the application
- `runtime.txt`: Specifies the Python version
- `heroku.yml`: Configuration for Docker-based deployment
- `init_db.py`: Script to initialize the database tables

### Making Changes

After making changes to your code, commit and push to Heroku:
```bash
git add .
git commit -m "Your commit message"
git push heroku main
```

### Pushing Updates to Heroku

To update your application on Heroku after making changes:

1. Make sure your changes are working locally:
   ```bash
   # Test your changes locally
   uvicorn backend.api:app --reload
   ```

2. Commit your changes to your local Git repository:
   ```bash
   # Stage your changes
   git add .
   
   # Commit your changes with a descriptive message
   git commit -m "Description of the changes made"
   ```

3. Push your changes to Heroku:
   ```bash
   # Push to Heroku's main branch
   git push heroku main
   ```

4. Verify your deployment:
   ```bash
   # Check the deployment logs
   heroku logs --tail --app quiz-maker-api
   
   # Open the application in a browser
   heroku open --app quiz-maker-api
   ```

5. If you've made database schema changes:
   ```bash
   # Run any necessary database migrations
   heroku run python migrations.py --app quiz-maker-api
   ```

6. If you need to restart the application:
   ```bash
   # Restart the application dynos
   heroku restart --app quiz-maker-api
   ```

7. Monitor your application for any issues:
   ```bash
   # Check application metrics
   heroku ps --app quiz-maker-api
   
   # View recent logs
   heroku logs --app quiz-maker-api
   ```

### Viewing Logs

To view application logs:
```bash
heroku logs --tail --app quiz-maker-api
```

## API Documentation

When the application is running, visit `http://localhost:8000/docs` (local) or `https://quiz-maker-api.herokuapp.com/docs` (Heroku) to view the interactive API documentation.