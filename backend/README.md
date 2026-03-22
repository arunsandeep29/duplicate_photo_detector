# Duplicate Photos Finder - Backend API

A Flask-based REST API for finding and managing duplicate photos in directories. Phase 1 implementation with core infrastructure, endpoints, and comprehensive testing.

## Features

- **Health Check Endpoint** - Monitor API status
- **Directory Scanning** - Scan directories for duplicate images
- **Duplicate Detection** - Identify duplicate image groups
- **File Operations** - Move or delete duplicate files
- **Comprehensive API Documentation** - OpenAPI/Swagger specification
- **Full Test Coverage** - 100% unit test coverage with pytest
- **Type Hints** - Full Python type annotations (3.9+)
- **CORS Support** - Enable frontend development at localhost:3000

## Project Structure

```
backend/
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── config.py                # Environment-based configuration
│   ├── main.py                  # Entry point
│   ├── exceptions.py            # Custom exception classes
│   ├── utils/
│   │   ├── __init__.py
│   │   └── validators.py        # Input validation functions
│   └── api/
│       ├── __init__.py
│       └── routes.py            # API endpoints
├── tests/
│   ├── conftest.py              # Pytest fixtures
│   └── test_api.py              # Comprehensive test suite
├── openapi.yaml                 # OpenAPI specification
├── requirements.txt             # Python dependencies
├── setup.py                     # Package configuration
├── Dockerfile                   # Docker configuration
├── .flake8                      # Flake8 linting config
├── pyproject.toml               # Black formatter config
├── .env.example                 # Environment variables template
└── README.md                    # This file
```

## Installation

### Prerequisites

- Python 3.9+
- pip or conda
- Optional: Docker

### Local Setup

1. **Clone the repository** (if not already done):
   ```bash
   cd backend
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env as needed
   ```

5. **Verify installation**:
   ```bash
   python -c "import flask; print(f'Flask {flask.__version__} installed')"
   ```

## Running the Application

### Local Development

```bash
# Start the Flask development server
python -m app.main

# The API will be available at http://localhost:5000
# Health check: http://localhost:5000/api/health
```

### With Environment Variables

```bash
# Set environment variables
export FLASK_ENV=development
export DEBUG=True

# Run the server
python -m app.main
```

## Running Tests

### Run All Tests

```bash
# Run tests with verbose output
pytest -v

# Run tests with coverage report
pytest --cov=app --cov-report=html

# Run specific test class
pytest tests/test_api.py::TestHealthEndpoint -v

# Run with specific markers
pytest -k "test_health" -v
```

### Test Coverage

To achieve 100% code coverage:

```bash
pytest --cov=app --cov-report=term-missing --cov-report=html tests/

# View coverage report
open htmlcov/index.html  # On macOS
start htmlcov/index.html # On Windows
```

Current test coverage includes:
- ✅ 20+ tests for API endpoints
- ✅ Happy path and error cases
- ✅ Input validation tests
- ✅ Error response format validation
- ✅ Edge cases (empty requests, invalid formats, etc.)

## Code Quality & Linting

### Format Code with Black

```bash
# Format all Python files
black app/ tests/

# Check formatting without changes
black --check app/ tests/
```

### Lint with Flake8

```bash
# Run flake8 linting
flake8 app/ tests/

# Show statistics
flake8 app/ tests/ --statistics
```

### Run Both in Sequence

```bash
black app/ tests/ && flake8 app/ tests/ && pytest -v
```

## API Documentation

### Interactive API Docs

When the server is running, access the OpenAPI specification:
- Raw OpenAPI YAML: See `openapi.yaml` in this directory
- Swagger UI: Can be added (e.g., via Flasgger) for interactive documentation

### API Endpoints

#### 1. Health Check
```
GET /api/health

Response (200):
{
  "status": "ok"
}
```

#### 2. Start Directory Scan
```
POST /api/scan

Request:
{
  "directory": "/path/to/photos"
}

Response (200):
{
  "scan_id": "scan-a1b2c3d4e5f6",
  "image_count": 42
}

Error (400):
{
  "error": "Directory does not exist",
  "code": "INVALID_REQUEST"
}
```

#### 3. Get Duplicates
```
GET /api/duplicates/<scan_id>

Response (200):
{
  "groups": [
    {
      "hash": "abc123def456",
      "original": "photo1.jpg",
      "copies": ["photo1_copy.jpg", "photo1_dup.jpg"]
    }
  ]
}

Error (404):
{
  "error": "Scan not found: scan-xyz",
  "code": "SCAN_NOT_FOUND"
}
```

#### 4. Move/Delete Duplicates
```
POST /api/move-duplicates

Request:
{
  "scan_id": "scan-a1b2c3d4e5f6",
  "destination": "/archive",
  "operations": [
    {
      "original": "photo1.jpg",
      "target_copy": "photo1_copy.jpg",
      "action": "move"
    }
  ]
}

Response (200):
{
  "moved_count": 1,
  "failed_count": 0,
  "errors": []
}
```

## Error Response Format

All error responses follow a consistent format:

```json
{
  "error": "Human-readable error message",
  "code": "MACHINE_READABLE_CODE",
  "details": "Optional additional information"
}
```

### Common Error Codes

- `INVALID_REQUEST` - Bad request, validation failed
- `MISSING_FIELD` - Required field missing from request
- `DIRECTORY_NOT_FOUND` - Specified directory doesn't exist
- `SCAN_NOT_FOUND` - Scan ID not found
- `PERMISSION_DENIED` - Permission denied for operation
- `INTERNAL_ERROR` - Unexpected server error

## Docker Setup

### Build Docker Image

```bash
docker build -t duplicate-photos:latest .
```

### Run Docker Container

```bash
# Run with default configuration
docker run -p 5000:5000 duplicate-photos:latest

# Run with environment variables
docker run -p 5000:5000 \
  -e FLASK_ENV=production \
  -e LOG_LEVEL=WARNING \
  duplicate-photos:latest

# Run with volume mounts for directories
docker run -p 5000:5000 \
  -v /path/to/photos:/photos \
  -v /app/uploads:/uploads \
  duplicate-photos:latest

# Run in background
docker run -d \
  --name duplicate-photos-api \
  -p 5000:5000 \
  duplicate-photos:latest
```

### Docker Compose (Optional)

Create a `docker-compose.yml` for easy orchestration:

```yaml
version: '3.9'
services:
  api:
    build: .
    ports:
      - "5000:5000"
    environment:
      FLASK_ENV: production
      LOG_LEVEL: INFO
    volumes:
      - ./uploads:/app/uploads
      - ./scans:/app/scans
```

Run with: `docker-compose up`

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_ENV` | development | Flask environment (development, testing, production) |
| `DEBUG` | False | Enable debug mode |
| `UPLOAD_DIR` | ./uploads | Directory for uploaded files |
| `TEMP_DIR` | ./temp | Directory for temporary files |
| `SCANS_DIR` | ./scans | Directory for scan data |
| `LOG_LEVEL` | INFO | Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |

### Configuration Classes

The app automatically selects configuration based on `FLASK_ENV`:

- **DevelopmentConfig** (default): DEBUG=True, LOG_LEVEL=DEBUG
- **TestingConfig**: TESTING=True, uses temp directories
- **ProductionConfig**: DEBUG=False, LOG_LEVEL=WARNING

## Development Workflow

1. **Make changes** to code
2. **Run tests**: `pytest -v`
3. **Check coverage**: `pytest --cov=app`
4. **Format code**: `black app/ tests/`
5. **Lint code**: `flake8 app/ tests/`
6. **Commit changes**: `git commit -m "Description"`

## Supported Image Formats

- JPEG (.jpg, .jpeg)
- PNG (.png)
- GIF (.gif)
- WebP (.webp)

## Troubleshooting

### Import Errors

```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Check Python version
python --version  # Should be 3.9+
```

### Port Already in Use

```bash
# Change port in code or run on different port
python -c "from app import create_app; app = create_app(); app.run(port=5001)"
```

### Test Failures

```bash
# Run specific test for debugging
pytest tests/test_api.py::TestHealthEndpoint::test_health_check_returns_200 -v

# Run with print statements
pytest -s tests/test_api.py
```

### CORS Issues

The API is configured to accept requests from:
- `http://localhost:3000`
- `http://127.0.0.1:3000`

Update `CORS_ORIGINS` in `app/config.py` for other origins.

## Performance Considerations

- Large directory scans may take time (optimize in Phase 2)
- Image hashing is CPU-intensive (consider async in Phase 2)
- Memory usage scales with image count (implement streaming in Phase 2)

## Security Considerations

- Directory paths are validated to prevent path traversal
- File operations are validated before execution
- All inputs are validated before processing
- Error messages don't leak sensitive information

## Future Enhancements (Phase 2+)

- Async image processing with Celery
- Database integration for persistent scan results
- Image similarity algorithm optimization
- Batch operations for large directories
- Progressive web app frontend integration
- Authentication and authorization
- Advanced filtering and grouping options

## Contributing

1. Follow PEP 8 style guide
2. Maintain 100% test coverage
3. Add docstrings to all functions
4. Use type hints throughout
5. Update README for new features

## License

MIT License - See LICENSE file for details

## Support

For issues, questions, or feature requests, please open an issue on GitHub.
