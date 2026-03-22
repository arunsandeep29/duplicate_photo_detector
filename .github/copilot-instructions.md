# Copilot Instructions for Duplicate Photos Finder

## Project Overview

A Python backend + React frontend application that identifies duplicate JPEG images by analyzing their content (not filenames) and moves copies to a user-specified directory.

**Architecture:**
- **Backend**: Python Flask server providing REST APIs for image scanning, duplicate detection, and file operations
- **Frontend**: React SPA allowing users to select source/destination directories and manage duplicate files
- **Core Algorithm**: Perceptual hashing (or content hashing) to identify duplicate images regardless of compression or metadata

## Build, Test, and Lint Commands

### Backend (Python)

```bash
# Install dependencies
cd backend
pip install -r requirements.txt

# Or with dev dependencies
pip install -e ".[dev]"

# Run linting
black app/  # Format code
flake8 app/ tests/  # Check style issues

# Run tests
pytest
pytest -v  # Verbose
pytest tests/test_image_comparison.py  # Single test file

# Run the development server
python -m app.main
```

### Frontend (React)

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm start

# Build for production
npm build

# Run tests
npm test

# Format and lint (add these to package.json as needed)
# npx eslint src/
# npx prettier --write src/
```

## Architecture and Key Components

### Backend Structure (`backend/app/`)

```
app/
├── main.py              # Flask app entry point
├── api/
│   ├── routes.py        # Flask route handlers
│   └── image_handler.py # Core image processing logic
├── services/
│   ├── image_processor.py   # Image hashing/comparison
│   ├── file_manager.py      # File operations (move/delete)
│   └── duplicate_finder.py  # Duplicate detection logic
└── models/
    └── image.py         # Image data structures
```

**Key Responsibilities:**
- **image_processor.py**: Computes perceptual/content hashes for images (using PIL)
- **duplicate_finder.py**: Compares hashes and groups duplicates
- **file_manager.py**: Moves/copies files with error handling
- **routes.py**: Exposes REST endpoints (scan, get_duplicates, move_duplicates, etc.)

### Frontend Structure (`frontend/src/`)

```
src/
├── App.jsx              # Main app component
├── components/
│   ├── DirectoryPicker.jsx      # Directory selection UI
│   ├── DuplicatesList.jsx       # Display duplicates
│   └── ResultsPanel.jsx         # Results and actions
├── services/
│   └── api.js           # API client (calls backend)
└── styles/
    └── App.css
```

**Key Responsibilities:**
- **DirectoryPicker**: Handles directory selection (via file dialog or path input)
- **DuplicatesList**: Displays found duplicates with previews
- **api.js**: Wraps fetch calls to backend endpoints

## Key Conventions

### Image Duplicate Detection Strategy

1. **Hashing Approach**: Use perceptual hashing (pHash) or simple content hashing for reliability
   - Perceptual hash: More robust to compression/minor edits
   - Content hash (SHA256): Exact content matching
   - Decision: Confirm which approach in initial implementation

2. **File Selection**: Only process JPEG files (.jpg, .jpeg extensions)
   - Validate MIME type if needed
   - Skip corrupted images gracefully

3. **Duplicate Grouping**: Group identical/similar images together
   - Keep original, mark copies
   - Use hash similarity threshold if using pHash (e.g., Hamming distance < 5)

### API Conventions

**Request/Response Format**: JSON

**Base Endpoints:**
- `POST /api/scan` - Scan directory for images
  - Body: `{ "directory": "/path/to/images" }`
  - Response: `{ "image_count": int, "scan_id": string }`

- `GET /api/duplicates/:scan_id` - Get duplicate groups
  - Response: `{ "groups": [{ "original": string, "copies": [string] }] }`

- `POST /api/move-duplicates` - Move duplicates to destination
  - Body: `{ "operations": [...], "destination": "/path" }`
  - Response: `{ "moved_count": int, "errors": [...] }`

**Error Responses:** Use HTTP status codes (400, 404, 500) with JSON error body:
```json
{ "error": "Description", "code": "ERROR_CODE" }
```

### File Organization Conventions

- **Backend Code**: Organize by feature (api, services, models) not layers
- **Frontend Components**: One component per file, co-locate styles if using CSS modules
- **Tests**: Mirror source structure (`backend/tests/services/test_duplicate_finder.py`)
- **Configuration**: Use `.env` files for paths/settings, committed `.env.example` for template

### Image Processing Notes

- **Performance**: For large directories, implement scanning with progress updates
- **Memory**: Stream large files or process in batches to avoid memory issues
- **Error Handling**: Handle corrupted JPEGs, permission errors, disk errors explicitly
- **Paths**: Cross-platform support (use `pathlib.Path` in Python, handle backslashes in React)

### Python Code Style

- **Naming**: snake_case for functions/variables, PascalCase for classes
- **Type Hints**: Use type hints for function signatures (Python 3.7+)
- **Docstrings**: Add docstrings to public functions/classes
- **Error Handling**: Custom exceptions in `app/exceptions.py`

```python
# Example pattern
from pathlib import Path
from typing import List

def find_duplicates(directory: str) -> List[ImageGroup]:
    """Find duplicate images in directory.
    
    Args:
        directory: Path to scan for JPEG files
        
    Returns:
        List of ImageGroup objects with duplicate information
        
    Raises:
        DirectoryNotFoundError: If directory doesn't exist
    """
    ...
```

### React Code Style

- **Components**: Functional components with hooks (no class components)
- **Naming**: PascalCase for components, camelCase for functions
- **State Management**: Use React hooks (useState, useContext) or consider Redux if complex
- **Props**: Validate with PropTypes or TypeScript if added
- **API Calls**: Use async/await pattern in useEffect hooks

```jsx
function DuplicatesList({ duplicateGroups, onMove }) {
  const [loading, setLoading] = useState(false);
  
  useEffect(() => {
    // fetch and process
  }, []);
  
  return (...);
}
```

## Common Tasks

### Adding a New Image Processing Algorithm
1. Create method in `backend/app/services/image_processor.py`
2. Add unit tests in `backend/tests/services/test_image_processor.py`
3. Update `duplicate_finder.py` to use new method
4. Test end-to-end via API

### Adding a New UI Feature
1. Create component in `frontend/src/components/`
2. Add API call methods to `frontend/src/services/api.js`
3. Update main `App.jsx` layout if needed
4. Test with backend running

### Running Specific Tests
- Backend single test file: `pytest backend/tests/services/test_image_processor.py`
- Frontend component: `npm test -- DuplicatesList.test.jsx`

## Environment Setup

- **Python Version**: 3.9+
- **Node Version**: 16+ (for React 18)
- **Port**: Backend runs on 5000, Frontend on 3000 (standard CRA)
- **Temp Storage**: Backend may need temp directory for processing

## Known Considerations

- **Large Directories**: Implement pagination/streaming for >1000 images
- **Symlinks**: Decide behavior for symbolic links (follow or skip)
- **Hidden Files**: May want to skip hidden/system files by default
- **Network Paths**: Consider network timeout for networked directories
- **Permissions**: Gracefully handle read/move permission errors
