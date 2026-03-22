# Phase 3-4 Parallel Development Coordination

**Date**: March 21, 2026  
**Status**: Parallel development in progress  
**Coordination**: Both teams can work independently - no blocking dependencies

---

## Overview

Phase 3 (Backend API Integration) and Phase 4 (Frontend UI) are proceeding in parallel with clear separation of concerns:

- **Phase 3**: Backend team integrating Phase 2 services into Flask routes
- **Phase 4**: Frontend team building React components and API client
- **Synchronization Point**: Both complete, then Phase 5 (E2E testing)

---

## Phase 3: Backend API Integration

### Responsibility
**Team**: Python Backend (@python-image-api-dev)

### Scope
1. Integrate Phase 2 services into Flask API endpoints
2. Implement scan result storage (in-memory acceptable)
3. Add comprehensive input validation
4. Ensure proper error handling and responses
5. Write integration tests (20-30 new tests)

### APIs Being Implemented

#### POST /api/scan
- **Input**: `{ "directory": "/path" }`
- **Output**: `{ "scan_id": "...", "image_count": 42 }`
- **Calls**: `batch_compute_hashes()` from ImageProcessor
- **Errors**: 400 Bad Request, 404 Not Found

#### GET /api/duplicates/{scan_id}
- **Input**: Scan ID from previous scan
- **Output**: `{ "groups": [{original, copies, hash}] }`
- **Calls**: `find_duplicates()` from DuplicateFinder
- **Errors**: 404 Not Found (invalid scan_id)

#### POST /api/move-duplicates
- **Input**: `{ "scan_id": "...", "destination": "...", "operations": [...] }`
- **Output**: `{ "moved_count": 5, "failed_count": 0, "errors": [] }`
- **Calls**: `execute_move_operations()` from FileManager
- **Errors**: 400 Bad Request, 404 Not Found, 500 Server Error

#### GET /api/health
- Already implemented in Phase 1
- Verify still works after integration

### Acceptance Criteria
- ✅ All 4 endpoints functional
- ✅ Phase 2 services properly integrated
- ✅ Input validation on all endpoints
- ✅ Error responses in correct format
- ✅ 20-30 new integration tests added
- ✅ All tests passing
- ✅ Code ready for Phase 4 integration

### Success Indicators
1. Can call `POST /api/scan` with valid directory → returns scan_id
2. Can call `GET /api/duplicates/{scan_id}` → returns groups
3. Can call `POST /api/move-duplicates` → executes operations
4. Invalid inputs return proper error responses
5. All existing tests still pass

---

## Phase 4: Frontend UI & Integration

### Responsibility
**Team**: UI Component Engineer (@ui-component-engineer)

### Scope
1. Create DirectoryPicker component
2. Create DuplicatesList component  
3. Create ActionsPanel component
4. Implement API client service
5. Wire up main App component
6. Write 60+ component tests

### Components Being Built

#### DirectoryPicker
- Input field for directory path
- Validation feedback
- Submit button to start scan
- Shows scan progress/results
- Integrates with `scanDirectory()` API call

#### DuplicatesList
- Displays groups from backend
- Shows original and copies
- Allows multi-select
- Responsive grid layout
- Integrates with `getDuplicates()` API call

#### ActionsPanel
- Shows selected operations count
- Destination directory input
- Move/Delete action buttons
- Progress display
- Integrates with `moveDuplicates()` API call

#### API Client Service (api.js)
```javascript
export async function scanDirectory(directory)
export async function getDuplicates(scanId)
export async function moveDuplicates(scanId, operations, destination)
export async function healthCheck()
```

### Acceptance Criteria
- ✅ All components functional
- ✅ API client service complete
- ✅ App component orchestrates workflow
- ✅ 60+ component tests written
- ✅ 80%+ test coverage
- ✅ Responsive design verified
- ✅ Error handling comprehensive
- ✅ Code ready for E2E testing

### Success Indicators
1. Can input directory path and start scan
2. Can view duplicate groups
3. Can select duplicates for move/delete
4. Can execute operations
5. Error messages displayed clearly
6. Works on desktop and tablet

---

## API Contract (Finalized - Won't Change)

All endpoints documented in **API_CONTRACT.md**

### Error Response Format
```json
{
  "error": "Human-readable message",
  "code": "ERROR_CODE",
  "details": "Optional additional context"
}
```

### Error Codes
- `BAD_REQUEST` - Invalid input
- `DIRECTORY_NOT_FOUND` - Directory doesn't exist
- `SCAN_NOT_FOUND` - Scan ID not found
- `PERMISSION_DENIED` - Permission error
- `INTERNAL_ERROR` - Server error

### HTTP Status Codes
- `200 OK` - Success
- `400 Bad Request` - Validation error
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

---

## Coordination Points

### Before Phase 3-4 Start
✅ API contract finalized (API_CONTRACT.md)  
✅ Phase 2 services complete and tested  
✅ Error codes documented  
✅ Response format agreed upon  

### During Phase 3-4 (Parallel)
- Both teams work independently
- No blocking dependencies
- Backend can mock data if needed
- Frontend can mock API if backend delays

### Integration Testing (Phase 5)
- Run both backend and frontend together
- Test full workflow end-to-end
- Verify error handling
- Performance testing with real images

---

## Timeline

| Milestone | Expected | Status |
|-----------|----------|--------|
| Phase 3 Complete | Today (~2-3 hours) | 🔄 In Progress |
| Phase 4 Complete | Today (~3-4 hours) | 🔄 In Progress |
| Phase 3+4 Integration | Tomorrow AM | ⏳ Queued |
| Phase 5 E2E Testing | Tomorrow PM | ⏳ Queued |
| Phase 6 Release Prep | Within 3 days | ⏳ Queued |

---

## Communication & Escalation

### Daily Standup (if needed)
- Phase 3 progress
- Phase 4 progress  
- Any blockers
- Integration readiness

### If Issues Arise
1. **Minor issues**: Teams resolve independently
2. **API contract issues**: Tech lead mediation
3. **Blocking issues**: Escalate immediately
4. **Integration gaps**: Surface in Phase 5 testing

### Code Review Process
- Phase 3: Tech lead reviews backend code
- Phase 4: Tech lead reviews frontend code
- Quality gates: Linting, tests, coverage targets

---

## Testing Strategy

### Phase 3 (Backend)
- Unit tests for service integration (already exist)
- New integration tests for API endpoints (20-30)
- Error case testing
- Target: 90%+ coverage

### Phase 4 (Frontend)
- Component tests (60+)
- API client tests
- Mock API for testing
- Target: 80%+ coverage

### Phase 5 (Integration)
- E2E tests with running backend
- Full workflow testing
- Error scenario testing
- Performance testing

---

## Success Criteria for Phases 3-4

✅ **Phase 3 Ready When:**
- All 4 endpoints working
- Phase 2 services integrated
- Input validation complete
- 20-30 tests added and passing
- Code review approved

✅ **Phase 4 Ready When:**
- All components built
- API client complete
- 60+ tests passing
- 80%+ coverage achieved
- Code review approved

✅ **Both Ready for Phase 5 When:**
- Phase 3 approved
- Phase 4 approved
- API contract verified
- Both teams confirm readiness

---

## Appendix: File Changes Summary

### Backend Changes (Phase 3)
- `backend/app/api/routes.py` - Add service integration
- `backend/app/__init__.py` - Add scan storage
- `backend/tests/test_api.py` - Add integration tests

### Frontend Changes (Phase 4)
- `frontend/src/components/DirectoryPicker.jsx`
- `frontend/src/components/DuplicatesList.jsx`
- `frontend/src/components/ActionsPanel.jsx`
- `frontend/src/services/api.js`
- `frontend/src/App.jsx`
- `frontend/src/components/__tests__/` - Component tests

---

**Status**: ON TRACK FOR COMPLETION THIS WEEK ✨

**Next Update**: When either Phase 3 or Phase 4 completes
