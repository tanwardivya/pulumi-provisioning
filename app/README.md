# FastAPI Application

FastAPI service for AWS S3 and RDS (PostgreSQL) operations.

## Features

- RESTful API endpoints for S3 operations (upload, download, list, delete)
- Database operations with PostgreSQL (create, read records)
- Health check endpoint
- Environment-based configuration
- Docker-ready

## Installation

```bash
# Install dependencies
uv pip install -e ".[dev]"

# Or with pip
pip install -e ".[dev]"
```

## Configuration

The application uses environment variables for configuration:

- `AWS_REGION`: AWS region (default: `us-east-1`)
- `S3_BUCKET_NAME`: S3 bucket name (required)
- `DB_HOST`: RDS endpoint (required)
- `DB_PORT`: Database port (default: `5432`)
- `DB_NAME`: Database name (required)
- `DB_USER`: Database username (required)
- `DB_PASSWORD`: Database password (required)

## Running Locally

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## API Endpoints

### Health Check
- `GET /health` - Application health status

### S3 Operations
- `GET /s3/list` - List all objects in S3 bucket
- `POST /s3/upload` - Upload file to S3
- `GET /s3/download/{key}` - Download file from S3
- `DELETE /s3/delete/{key}` - Delete file from S3

### Database Operations
- `GET /db/status` - Check database connection
- `POST /db/create` - Create a new record
- `GET /db/read` - Read all records
- `GET /db/read/{id}` - Read a specific record

## Docker

The application is containerized and can be run with Docker:

```bash
docker build -t fastapi-app .
docker run -p 8000:8000 \
  -e S3_BUCKET_NAME=your-bucket \
  -e DB_HOST=your-rds-endpoint \
  -e DB_NAME=your-db \
  -e DB_USER=your-user \
  -e DB_PASSWORD=your-password \
  fastapi-app
```

## Development

```bash
# Format code
black .

# Lint code
ruff check .

# Run tests
pytest
```

## Dependencies

See `pyproject.toml` for complete dependency list. Main dependencies:

- `fastapi`: Web framework
- `uvicorn`: ASGI server
- `boto3`: AWS SDK
- `sqlalchemy`: ORM
- `psycopg2-binary`: PostgreSQL driver
- `pydantic`: Data validation



