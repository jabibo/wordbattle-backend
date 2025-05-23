# Docker Deployment Guide

This guide explains how to deploy the WordBattle backend using Docker.

## Prerequisites

- Docker
- Docker Compose

## Quick Start

1. Clone the repository:
```bash
git clone https://github.com/yourusername/wordbattle-backend.git
cd wordbattle-backend
```

2. Start the application:
```bash
docker-compose up -d
```

3. The API will be available at http://localhost:8000

## Configuration

The Docker setup uses environment variables defined in the `docker-compose.yml` file. You can override these by:

1. Creating a `.env` file in the project root
2. Modifying the `docker-compose.yml` file directly

## Data Persistence

The application uses two volumes for data persistence:

1. `./data:/app/data` - Mounts the local data directory to the container for wordlists
2. `sqlite_data:/app/sqlite_data` - Docker volume for the SQLite database

## Logs

To view logs:
```bash
docker-compose logs -f
```

## Rebuilding the Container

If you make changes to the code, you need to rebuild the container:
```bash
docker-compose build
docker-compose up -d
```

## Stopping the Container

To stop the application:
```bash
docker-compose down
```

To stop and remove all data (including the database):
```bash
docker-compose down -v
```

## Troubleshooting

### Database Issues

If you encounter database issues:
1. Check the logs:
```bash
docker-compose logs -f
```

2. Access a shell in the container:
```bash
docker-compose exec app bash
```

3. Verify the database file exists:
```bash
ls -la /app/sqlite_data/
```

### Application Errors

1. Check application logs:
```bash
docker-compose logs app
```

2. Verify environment variables:
```bash
docker-compose exec app env
```

3. Restart the container:
```bash
docker-compose restart
```