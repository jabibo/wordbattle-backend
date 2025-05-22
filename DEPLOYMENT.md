# Deployment Guide

This guide explains how to deploy the WordBattle backend to various environments.

## Prerequisites

- Python 3.9+
- PostgreSQL (recommended for production) or SQLite
- Virtual environment tool (venv, conda, etc.)

## Local Development Deployment

1. Clone the repository:
```bash
git clone https://github.com/yourusername/wordbattle-backend.git
cd wordbattle-backend
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file:
```bash
cp .env.example .env
# Edit .env with your settings
```

5. Set up the database:
```bash
python -m app.create_tables --create
```

6. Run the development server:
```bash
uvicorn app.main:app --reload
```

## Production Deployment

### Using Docker

1. Build the Docker image:
```bash
docker build -t wordbattle-backend .
```

2. Run the container:
```bash
docker run -d -p 8000:8000 \
  --env-file .env \
  --name wordbattle-backend \
  wordbattle-backend
```

### Using a VPS or Dedicated Server

1. Set up a Python environment:
```bash
python -m venv /opt/wordbattle-venv
source /opt/wordbattle-venv/bin/activate
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
# Create a .env file or set variables in your system
export DATABASE_URL=postgresql://user:password@localhost/wordbattle
export SECRET_KEY=your-secure-secret-key
# Add other variables as needed
```

3. Set up the database:
```bash
# For PostgreSQL
createdb wordbattle
alembic upgrade head
```

4. Configure a production ASGI server:
```bash
# Install Gunicorn
pip install gunicorn uvicorn[standard]

# Run with Gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app
```

5. Set up a reverse proxy (Nginx example):
```nginx
server {
    listen 80;
    server_name api.wordbattle.example.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

6. Set up a systemd service:
```ini
[Unit]
Description=WordBattle Backend
After=network.target

[Service]
User=wordbattle
Group=wordbattle
WorkingDirectory=/path/to/wordbattle-backend
Environment="PATH=/opt/wordbattle-venv/bin"
EnvironmentFile=/path/to/wordbattle-backend/.env
ExecStart=/opt/wordbattle-venv/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app

[Install]
WantedBy=multi-user.target
```

### Using a PaaS (Heroku example)

1. Create a Heroku app:
```bash
heroku create wordbattle-backend
```

2. Add a PostgreSQL database:
```bash
heroku addons:create heroku-postgresql:hobby-dev
```

3. Set environment variables:
```bash
heroku config:set SECRET_KEY=your-secure-secret-key
# Add other variables as needed
```

4. Deploy the application:
```bash
git push heroku main
```

5. Run migrations:
```bash
heroku run alembic upgrade head
```

## Security Considerations

1. Always use HTTPS in production
2. Generate a strong SECRET_KEY
3. Use a production-ready database (PostgreSQL recommended)
4. Set up proper rate limiting
5. Configure CORS appropriately
6. Regularly update dependencies

## Monitoring and Maintenance

1. Set up logging:
```python
# In your application
import logging
logging.basicConfig(level=logging.INFO)
```

2. Use a monitoring service (e.g., Sentry, Datadog)

3. Set up regular database backups

4. Implement health check endpoints

5. Schedule regular dependency updates