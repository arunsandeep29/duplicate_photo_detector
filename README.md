# Duplicate Photos Finder

A Python backend + React frontend application that identifies and moves duplicate JPEG images based on content analysis.

## Architecture Overview

- **Backend**: Python Flask/FastAPI server handling image processing
- **Frontend**: React SPA for directory selection and duplicate management
- **Core Feature**: Content-based image comparison (hashing) to find duplicates

## Quick Start

### Backend
```bash
cd backend
pip install -r requirements.txt
python -m app.main
```

### Frontend
```bash
cd frontend
npm install
npm start
```

## Project Structure

```
duplicate_photos/
├── backend/          # Python backend
│   ├── app/         # Application code
│   ├── tests/       # Test files
│   ├── requirements.txt
│   └── setup.py
├── frontend/        # React frontend
│   ├── src/
│   ├── public/
│   └── package.json
└── .github/
    └── copilot-instructions.md
```
