# 🚀 Development Server Startup Guide

## Overview

This guide explains how to start both the backend (Flask) and frontend (React) servers for the Duplicate Photos Finder application.

### Quick Start

Choose your approach based on your operating system and preferences:

#### **macOS/Linux - Recommended**
```bash
./start-dev.sh both
```

#### **Windows**
```batch
start-dev.bat
```

#### **Any OS (Node.js)**
```bash
node start-dev.js both
```

#### **Makefile (macOS/Linux)**
```bash
make start
```

---

## Option 1: Bash Script (macOS/Linux)

**File**: `start-dev.sh`

### Usage
```bash
# Start both servers
./start-dev.sh both

# Start only backend
./start-dev.sh backend

# Start only frontend
./start-dev.sh frontend
```

### Features
- ✅ Automatic virtual environment setup
- ✅ Automatic npm dependency installation
- ✅ Clean startup with color-coded output
- ✅ Graceful shutdown (Ctrl+C)
- ✅ Shows URLs for quick access

### Requirements
- Python 3.7+
- Node.js 16+
- npm

---

## Option 2: Windows Batch Script

**File**: `start-dev.bat`

### Usage
```batch
# Start both servers in separate windows
start-dev.bat

# Or double-click the file
```

### Features
- ✅ Launches servers in separate windows
- ✅ Automatic virtual environment setup
- ✅ Automatic npm dependency installation
- ✅ Easy to use (just double-click!)

### Notes
- Each server opens in its own Command Prompt window
- Close windows individually or all at once
- Virtual environment is created automatically on first run

---

## Option 3: Node.js Script (Cross-Platform)

**File**: `start-dev.js`

### Usage
```bash
# Start both servers
node start-dev.js both

# Start only backend
node start-dev.js backend

# Start only frontend
node start-dev.js frontend
```

### Features
- ✅ Works on Windows, macOS, and Linux
- ✅ Automatic npm dependency installation
- ✅ Streaming output from both servers
- ✅ Clean process management

### Requirements
- Node.js 12+

---

## Option 4: Makefile (macOS/Linux)

**File**: `Makefile`

### Usage
```bash
# See all available commands
make help

# Start both servers
make start

# Start only backend
make start-backend

# Start only frontend
make start-frontend

# Run all tests
make test

# Lint all code
make lint

# Build frontend for production
make build
```

### Other Makefile Commands
```bash
make setup           # Install dependencies
make test-backend    # Run backend tests only
make test-frontend   # Run frontend tests only
make lint-backend    # Lint backend code
make lint-frontend   # Lint frontend code
make clean           # Remove build artifacts
```

---

## Manual Setup (If Scripts Don't Work)

### Backend Setup
```bash
cd backend

# Create virtual environment (first time only)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies (first time only)
pip install -e ".[dev]"

# Start server
python -m app.main
```

**Backend runs on**: `http://localhost:5000`

### Frontend Setup
```bash
cd frontend

# Install dependencies (first time only)
npm install

# Start development server
npm start
```

**Frontend runs on**: `http://localhost:3000`

---

## Accessing the Application

Once both servers are running:

### Frontend
- **URL**: http://localhost:3000
- **Open this in your browser to use the application**

### Backend API
- **Health Check**: http://localhost:5000/api/health
- **Expected response**: `{"status": "ok"}`

---

## Troubleshooting

### "Python not found"
- Install Python 3.7+ from https://www.python.org
- Verify: `python --version`

### "npm not found"
- Install Node.js 16+ from https://nodejs.org
- Verify: `npm --version`

### "Port already in use"
- Backend: Kill process using port 5000
- Frontend: Kill process using port 3000

**macOS/Linux**:
```bash
lsof -i :5000   # Find process on port 5000
kill -9 <PID>   # Kill the process
```

**Windows**:
```batch
netstat -ano | findstr :5000        # Find process on port 5000
taskkill /PID <PID> /F              # Kill the process
```

### Virtual environment issues
```bash
cd backend
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

### npm issues
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

---

## Development Workflow

### 1. **Start Both Servers**
```bash
./start-dev.sh both  # or other script option
```

### 2. **Work on Code**
- Backend: Edit files in `backend/app/`
- Frontend: Edit files in `frontend/src/`
- Both will auto-reload on file changes

### 3. **Run Tests During Development**
```bash
# In separate terminal
make test            # All tests
make test-backend    # Backend only
make test-frontend   # Frontend only
```

### 4. **Check Code Quality**
```bash
# In separate terminal
make lint            # Check all code
make lint-backend    # Backend only
make lint-frontend   # Frontend only
```

### 5. **Stop Servers**
- **Bash/Node script**: Press `Ctrl+C`
- **Windows batch**: Close the Command Prompt windows
- **Make**: Press `Ctrl+C` in the terminal

---

## Advanced Usage

### Running Tests While Servers Run
```bash
# Terminal 1: Start servers
./start-dev.sh both

# Terminal 2: Run tests
make test
```

### Building for Production
```bash
# Build frontend
make build

# Output: frontend/build/
# Ready to deploy!
```

### Testing API Endpoints
```bash
# Health check
curl http://localhost:5000/api/health

# Scan a directory
curl -X POST http://localhost:5000/api/scan \
  -H "Content-Type: application/json" \
  -d '{"directory": "/path/to/images"}'
```

---

## Environment Variables

### Backend
Create `backend/.env`:
```
FLASK_ENV=development
FLASK_DEBUG=1
```

### Frontend
Create `frontend/.env`:
```
REACT_APP_API_URL=http://localhost:5000
REACT_APP_DEBUG=true
```

---

## Next Steps

1. ✅ **Start both servers** using one of the script options
2. ✅ **Open frontend** at http://localhost:3000
3. ✅ **Verify backend** by visiting http://localhost:5000/api/health
4. ✅ **Test the application** by selecting a directory with images
5. ✅ **Run tests** with `make test` to verify everything works

---

## Documentation

- **API Contract**: See `API_CONTRACT.md`
- **Backend Setup**: See `backend/README.md`
- **Frontend Setup**: See `frontend/README.md`
- **Full Project Guide**: See `README.md`

---

## Support

If servers don't start:
1. Check all requirements are installed
2. Try the manual setup steps above
3. Check error messages carefully
4. Verify ports 5000 and 3000 are available
5. Try a different script option

---

**Ready to start? Run**: `./start-dev.sh both` (or your preferred option)

Happy developing! 🚀
