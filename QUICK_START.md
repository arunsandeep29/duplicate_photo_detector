# Quick Start Guide - Duplicate Photos Finder Backend

## 🚀 Get Started in 5 Minutes

### 1. Install Dependencies (1 minute)
```bash
cd backend
pip install -r requirements.txt
```

### 2. Run Tests (30 seconds)
```bash
pytest -v
# 55 tests should pass ✓
```

### 3. Start the Server (30 seconds)
```bash
python -m app.main
# Server runs on http://localhost:5000
```

### 4. Test an Endpoint (1 minute)
```bash
# In another terminal
curl http://localhost:5000/api/health
# Response: {"status": "ok"}
```

### 5. View API Documentation (1 minute)
Check `backend/openapi.yaml` or read `backend/README.md`

---

## 📋 Common Commands

### Development
```bash
# Start development server
python -m app.main

# Run all tests
pytest -v

# Run tests with coverage
pytest --cov=app --cov-report=html

# Check code formatting
black --check app/ tests/

# Fix code formatting
black app/ tests/

# Check linting
flake8 app/ tests/
```

### Testing Specific Endpoints
```bash
# Health check
curl http://localhost:5000/api/health

# Start a scan (with valid directory path)
curl -X POST http://localhost:5000/api/scan \
  -H "Content-Type: application/json" \
  -d '{"directory": "/path/to/photos"}'

# Get duplicates (after getting scan_id from above)
curl http://localhost:5000/api/duplicates/scan-abc123

# Move duplicates
curl -X POST http://localhost:5000/api/move-duplicates \
  -H "Content-Type: application/json" \
  -d '{
    "scan_id": "scan-abc123",
    "destination": "/archive",
    "operations": [{
      "original": "photo1.jpg",
      "target_copy": "photo1_copy.jpg",
      "action": "move"
    }]
  }'
```

### Docker
```bash
# Build image
docker build -t duplicate-photos:latest .

# Run container
docker run -p 5000:5000 duplicate-photos:latest

# Run with volume mounts
docker run -p 5000:5000 \
  -v /path/to/photos:/photos \
  duplicate-photos:latest
```

---

## 📚 API Endpoints

### GET /api/health
Health check - Always returns 200
```
curl http://localhost:5000/api/health
{"status": "ok"}
```

### POST /api/scan
Start scanning a directory
```json
Request: {
  "directory": "/path/to/photos"
}
Response: {
  "scan_id": "scan-a1b2c3d4e5f6",
  "image_count": 42
}
```

### GET /api/duplicates/{scan_id}
Get duplicate groups from a completed scan
```json
Response: {
  "groups": [
    {
      "hash": "abc123",
      "original": "photo1.jpg",
      "copies": ["photo1_copy.jpg", "photo1_dup.jpg"]
    }
  ]
}
```

### POST /api/move-duplicates
Execute operations on duplicate files
```json
Request: {
  "scan_id": "scan-abc123",
  "destination": "/archive",
  "operations": [
    {
      "original": "photo1.jpg",
      "target_copy": "photo1_copy.jpg",
      "action": "move"
    }
  ]
}
Response: {
  "moved_count": 1,
  "failed_count": 0,
  "errors": []
}
```

---

## ⚙️ Configuration

### Environment Variables (.env)
```
FLASK_ENV=development
DEBUG=True
UPLOAD_DIR=./uploads
TEMP_DIR=./temp
SCANS_DIR=./scans
LOG_LEVEL=DEBUG
```

### CORS Configuration
Currently allows:
- `http://localhost:3000`
- `http://127.0.0.1:3000`

Edit `app/config.py` to add more origins

---

## 🧪 Testing

### Run All Tests
```bash
pytest -v
```

### Run Specific Test Class
```bash
pytest tests/test_api.py::TestHealthEndpoint -v
```

### Run with Coverage
```bash
pytest --cov=app --cov-report=html
open htmlcov/index.html  # View report
```

### Run Specific Test
```bash
pytest tests/test_api.py::TestHealthEndpoint::test_health_check_returns_200 -v
```

---

## 📊 Test Results
- ✅ 55 tests passing
- ✅ 85% code coverage
- ✅ 0 flake8 violations
- ✅ Black formatting compliant

---

## 🔧 Troubleshooting

### Port 5000 Already in Use
```bash
# Use a different port
python -c "from app import create_app; app = create_app(); app.run(port=5001)"
```

### Import Errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Directory Not Found Error
Use absolute paths for directory scanning:
```bash
# Good
/home/user/Photos
C:\Users\user\Pictures

# Not good
~/Photos
.\Pictures
```

---

## 📖 Documentation

- **API Endpoints**: See `backend/README.md` - "API Documentation" section
- **OpenAPI Spec**: See `backend/openapi.yaml`
- **Configuration**: See `backend/README.md` - "Configuration" section
- **Docker**: See `backend/README.md` - "Docker Setup" section

---

## 🎯 What's Next?

1. **Local Testing**: Start the server and test endpoints
2. **Frontend Integration**: Connect to React frontend on localhost:3000
3. **Phase 2**: Implement actual duplicate detection
4. **Deployment**: Use Docker to deploy to production

---

## ✅ Quality Checks

Always run before committing:
```bash
# Format code
black app/ tests/

# Check linting
flake8 app/ tests/

# Run tests
pytest -v

# Combined
black app/ tests/ && flake8 app/ tests/ && pytest -v
```

---

## 📞 Support

For issues or questions, check:
1. `backend/README.md` - Troubleshooting section
2. `PHASE_1_COMPLETE.md` - Implementation details
3. `IMPLEMENTATION_SUMMARY.md` - Full documentation

---

**Ready to go!** 🚀
