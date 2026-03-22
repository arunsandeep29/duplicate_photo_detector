# Duplicate Photos Finder - Frontend

A React-based SPA (Single Page Application) for identifying and managing duplicate JPEG images.

## Project Overview

This is the frontend component of the Duplicate Photos Finder project. It provides an intuitive user interface for:
- Selecting directories to scan for duplicate images
- Monitoring scan progress
- Reviewing and managing duplicate image groups
- Moving or deleting duplicate files

## Prerequisites

- **Node.js**: Version 16 or higher
- **npm**: Version 7 or higher
- **Backend**: The backend API must be running on `http://localhost:5000` (configurable via environment variables)

## Installation

```bash
# Install dependencies
npm install

# Copy environment configuration
cp .env.example .env.development.local
```

## Development

### Start Development Server

```bash
npm start
```

The application will start on `http://localhost:3000` and automatically open in your browser.

### Lint Code

Check for TypeScript and ESLint errors:

```bash
npm run lint
```

Fix linting issues automatically:

```bash
npm run lint:fix
```

### Format Code

Format code with Prettier:

```bash
npm run format
```

## Testing

### Run Tests

Execute the test suite in watch mode:

```bash
npm test
```

### Run Tests with Coverage

Generate coverage report:

```bash
npm test -- --coverage
```

This generates a coverage report showing line, branch, and statement coverage percentages.

## Building

### Build for Production

```bash
npm run build
```

This creates an optimized production build in the `build/` directory.

## Docker

### Build Docker Image

```bash
docker build -t duplicate-photos-frontend .
```

### Run Docker Container

```bash
docker run -p 3000:3000 duplicate-photos-frontend
```

The application will be available at `http://localhost:3000`.

## API Client Documentation

The frontend includes a comprehensive API client service (`src/services/api.ts`) that handles communication with the backend.

### Supported Endpoints

#### 1. Scan Directory
```typescript
scanDirectory(directory: string): Promise<ScanResponse | ApiError>
```
- **Method**: POST `/api/scan`
- **Request**: `{directory: string}`
- **Response**: `{scan_id: string, image_count: number}`
- **Errors**: Returns `ApiError` on failure

#### 2. Get Duplicates
```typescript
getDuplicates(scanId: string): Promise<DuplicatesResponse | ApiError>
```
- **Method**: GET `/api/duplicates/:scanId`
- **Response**: `{groups: Array<Array<{file_path: string, size: number}>>}`
- **Errors**: Returns `ApiError` on failure

#### 3. Move Duplicates
```typescript
moveDuplicates(
  scanId: string,
  operations: Array<{source: string, destination: string}>,
  destination: string
): Promise<MoveDuplicatesResponse | ApiError>
```
- **Method**: POST `/api/move-duplicates`
- **Request**: `{scan_id: string, operations: Array, destination: string}`
- **Response**: `{moved_count: number, failed_count: number}`
- **Errors**: Returns `ApiError` on failure

#### 4. Health Check
```typescript
healthCheck(): Promise<HealthCheckResponse | ApiError>
```
- **Method**: GET `/api/health`
- **Response**: `{status: string, backend_version?: string}`
- **Errors**: Returns `ApiError` on failure

### Error Handling

All API client methods return a union type that can be either a successful response or an `ApiError`:

```typescript
interface ApiError {
  error: string;      // Human-readable error message
  status: number;     // HTTP status code (0 for network/timeout errors)
}
```

### Error Scenarios Handled

The API client comprehensively handles the following error scenarios:

| Error Type | Status | Example |
|-----------|--------|---------|
| Network Error | 0 | `{error: "CORS error - backend not responding", status: 0}` |
| Timeout (30s) | 0 | `{error: "Request timeout", status: 0}` |
| Invalid JSON | 0 | `{error: "Invalid response format", status: 0}` |
| HTTP 400 | 400 | `{error: "Invalid directory path", status: 400}` |
| HTTP 404 | 404 | `{error: "Resource not found", status: 404}` |
| HTTP 500 | 500 | `{error: "Server error", status: 500}` |
| Missing Fields | 0 | `{error: "Missing required field: scan_id", status: 0}` |
| CORS Errors | 0 | `{error: "CORS error - backend not responding", status: 0}` |

### Usage Example

```typescript
import { apiClient } from './services/api';

// Scan a directory
const result = await apiClient.scanDirectory('/path/to/images');

if ('error' in result) {
  // Handle error
  console.error(`Error: ${result.error} (Status: ${result.status})`);
} else {
  // Use response
  console.log(`Scan started. ID: ${result.scan_id}, Images: ${result.image_count}`);
}
```

## Environment Configuration

### Available Environment Variables

- `REACT_APP_API_BASE_URL` - Base URL for the backend API (default: `http://localhost:5000`)

### Configuration Files

- `.env.example` - Example environment variables (commit to repository)
- `.env.development.local` - Development environment variables (add to `.gitignore`, don't commit)

## Code Standards

### TypeScript

- Strict mode enabled (`noImplicitAny: true`)
- No `any` types allowed
- Type-safe throughout the codebase

### ESLint Configuration

- React rules enabled
- TypeScript rules enabled
- Strict mode enforced

### Prettier Formatting

- 2-space indentation
- Single quotes for strings
- Trailing commas for multi-line arrays/objects
- 80-character line width

## Project Structure

```
frontend/
├── public/              # Static assets
│   └── index.html      # HTML entry point
├── src/
│   ├── components/     # React components
│   │   ├── DirectoryPicker.tsx
│   │   ├── ScanProgress.tsx
│   │   └── DuplicatesList.tsx
│   ├── services/       # API client and services
│   │   ├── api.ts
│   │   └── api.test.ts
│   ├── styles/         # CSS styles
│   │   └── App.css
│   ├── App.tsx         # Main app component
│   ├── App.test.tsx    # App tests
│   ├── index.tsx       # React entry point
│   └── index.css       # Global styles
├── .env.example        # Example environment variables
├── .env.development.local # Development environment variables
├── .eslintrc.json      # ESLint configuration
├── .gitignore          # Git ignore rules
├── .prettierrc          # Prettier formatting rules
├── Dockerfile          # Docker configuration
├── package.json        # npm dependencies and scripts
├── tsconfig.json       # TypeScript configuration
└── README.md           # This file
```

## Coordination with Backend Team

### API Contract

The API contract between frontend and backend is defined in `src/services/api.ts` with full TypeScript interfaces for all request/response types. Before making changes to API endpoints:

1. **Notify the backend team** of any endpoint modifications
2. **Update the TypeScript interfaces** in `src/services/api.ts`
3. **Add/update tests** in `src/services/api.test.ts`
4. **Update this documentation** if error handling changes

### Integration Testing

When both frontend and backend are running:
1. Backend: `python -m backend.main` (or `npm run dev` for backend)
2. Frontend: `npm start`
3. Run full integration: `npm test`

## Troubleshooting

### Backend Connection Issues

If you see "⚠ Disconnected" status:

1. **Verify backend is running**:
   ```bash
   curl http://localhost:5000/api/health
   ```

2. **Check environment configuration**:
   ```bash
   cat .env.development.local
   ```

3. **Verify API base URL**:
   - Ensure `REACT_APP_API_BASE_URL` points to correct backend URL
   - Restart dev server after changing env variables

### Port Already in Use

If port 3000 is already in use:
```bash
# Specify a different port
PORT=3001 npm start
```

### Test Coverage Issues

If coverage is below 70%:
```bash
npm test -- --coverage --watchAll=false
```

Review uncovered code and add tests as needed.

## Phase 1 Status

✅ React SPA bootstrap with TypeScript  
✅ API client service with comprehensive error handling  
✅ Stub components created (to be implemented in Phase 4)  
✅ Environment configuration  
✅ ESLint and Prettier configuration  
✅ Testing setup with minimum coverage requirements  
✅ Docker support  
✅ Documentation complete  

## Next Phase

Phase 4 will implement the full UI components:
- Interactive directory picker with file browser
- Real-time scan progress display
- Duplicate image gallery with previews
- Action buttons for file operations
- Responsive design for desktop and tablet

## License

See LICENSE file for details.

## Support

For issues or questions, open a GitHub issue or contact the team.
