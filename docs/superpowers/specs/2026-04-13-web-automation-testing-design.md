# Web Automation Testing Feature Design

**Date:** 2026-04-13
**Status:** Approved
**Author:** Claude Sonnet

## Overview

Add a web automation testing feature that allows users to create browser-based tests using natural language descriptions. Users submit a URL and test description, and the system executes the test using Claude CLI's browser automation capabilities, providing real-time feedback through WebSocket connections.

## Requirements

### Functional Requirements

1. **Test Creation**: Users can create tests by providing a URL and natural language description
2. **Test Execution**: Backend executes tests asynchronously using local Claude CLI
3. **Real-time Feedback**: WebSocket connection streams execution logs in real-time
4. **Test Management**: Users can view, delete, and retry their tests
5. **Result Storage**: Test results, logs, and screenshots are persisted in the database
6. **User Isolation**: Users can only access their own tests

### Non-Functional Requirements

1. **Performance**: Support up to 3 concurrent test executions (configurable)
2. **Timeout**: Default test timeout of 10 minutes (configurable)
3. **Security**: URL validation, private network blocking, user authentication required
4. **Scalability**: Independent module architecture allows future expansion

## Architecture

### System Components

```
Frontend (React)
├── Test List Page
├── Create Test Form
├── Test Detail Page
└── WebSocket Client

Backend API (FastAPI)
├── REST API (/api/web-tests/*)
├── WebSocket (/ws/web-tests/{test_id})
└── Background Task Runner

External Dependencies
└── Local Claude CLI
```

### Data Flow

1. User creates test via form (URL + description)
2. Backend creates test record (status: pending)
3. Background task starts, invokes Claude CLI
4. WebSocket connection established for real-time updates
5. Executor parses Claude output, extracts structured data
6. Results saved to database
7. User views complete results in detail page

## Data Models

### Database Tables

#### web_tests

```python
class WebTest(SQLModel, table=True):
    id: uuid.UUID (primary key)
    url: str (max_length=2048)
    description: str (max_length=5000)
    status: Literal["pending", "running", "completed", "failed", "cancelled"]
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    owner_id: uuid.UUID (foreign_key -> user.id, on_delete=CASCADE)
    owner: User (Relationship)
    results: list[WebTestResult] (Relationship)
```

#### web_test_results

```python
class WebTestResult(SQLModel, table=True):
    id: uuid.UUID (primary key)
    test_id: uuid.UUID (foreign_key -> webtest.id, on_delete=CASCADE)
    test: WebTest (Relationship)

    # Structured results
    success: bool
    error_message: str | None
    screenshot_path: str | None  # MinIO path (mandatory if test completes)
    video_path: str | None  # MinIO path (optional, for future video recording feature)

    # Complete log stream
    execution_logs: str

    # Execution metadata
    execution_duration: float | None  # seconds
    claude_version: str | None
    created_at: datetime
```

### API Schemas

```python
class WebTestCreate(SQLModel):
    url: str (max_length=2048)
    description: str (min_length=10, max_length=5000)

class WebTestPublic(SQLModel):
    id: uuid.UUID
    url: str
    description: str
    status: Literal["pending", "running", "completed", "failed", "cancelled"]
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    owner_id: uuid.UUID
    has_result: bool

class WebTestResultPublic(SQLModel):
    id: uuid.UUID
    test_id: uuid.UUID
    success: bool
    error_message: str | None
    screenshot_url: str | None  # MinIO signed URL
    video_url: str | None
    execution_logs: str
    execution_duration: float | None
    created_at: datetime
```

## API Design

### REST Endpoints

#### POST /api/web-tests/
- **Auth**: Required
- **Body**: `WebTestCreate`
- **Response**: 201 Created + `WebTestPublic`
- **Side Effect**: Creates test record, starts background execution

#### GET /api/web-tests/
- **Auth**: Required
- **Query**: `skip=0, limit=50, status=optional`
- **Response**: 200 OK + `WebTestsPublic`
- **Logic**: Returns current user's tests, ordered by created_at DESC

#### GET /api/web-tests/{id}
- **Auth**: Required + ownership check
- **Response**: 200 OK + `WebTestPublic`

#### DELETE /api/web-tests/{id}
- **Auth**: Required + ownership check
- **Validation**: Only pending/failed tests can be deleted
- **Side Effect**: Cancels if running, deletes record and results

#### POST /api/web-tests/{id}/retry
- **Auth**: Required + ownership check
- **Logic**: Creates new test with same URL and description
- **Response**: 201 Created + new `WebTestPublic`

#### GET /api/web-tests/{id}/result
- **Auth**: Required + ownership check
- **Response**: 200 OK + `WebTestResultPublic`

### WebSocket Endpoint

#### /ws/web-tests/{test_id}
- **Auth**: Token via query parameter (`?token=xxx`)
- **Validation**: Ownership check required
- **Message Types**:
  ```json
  {"type": "log", "data": "log content..."}
  {"type": "status", "data": "running"}
  {"type": "screenshot", "data": "https://minio.xxx/screenshot.png"}
  {"type": "complete", "data": {"success": true, "duration": 45.2}}
  {"type": "error", "data": "error message"}
  ```

## Frontend Design

### Pages

#### 1. Test List Page (/web-tests)
- Table with columns: URL, Status, Created, Actions
- Filter by status (All, Pending, Running, Completed)
- "New Test" button opens create dialog
- Row actions: View, Retry, Delete (based on status)

#### 2. Create Test Dialog
- Form fields:
  - Target URL (required, validated)
  - Test Description (required, 10-5000 chars)
- Auto-focus on URL field
- Character counter for description
- Submit button disabled while creating

#### 3. Test Detail Page
- Header: URL, status badge, timestamps, action buttons
- Result Summary: Success/failure indicator, screenshot preview
- Execution Log Viewer:
  - Auto-scroll to bottom (toggleable)
  - Color-coded lines (success=green, error=red)
  - Timestamp for each log entry
  - Collapsible sections

### Components

```
frontend/src/components/WebTests/
├── TestList.tsx           # Table with filtering
├── CreateTestForm.tsx     # Form with validation
├── TestDetail.tsx         # Detail view with logs
├── LogViewer.tsx          # Log display component
├── StatusBadge.tsx        # Status indicator badge
└── testColumns.tsx        # Table column definitions
```

### WebSocket Hook

```typescript
// hooks/useWebSocketLog.ts
interface UseWebSocketLogOptions {
  onLog: (log: string) => void
  onStatus: (status: string) => void
  onComplete: (result: CompletionResult) => void
  onError: (error: string) => void
}

// Features:
// - Auto-reconnect with exponential backoff
// - Max retry attempts: 10
// - Cleanup on unmount
// - Token-based auth
```

## Claude CLI Integration

### Command Construction

```bash
claude "Use browser automation to test this website: ${url}

Test description:
${description}

Please:
1. Navigate to the URL
2. Perform the tests described above
3. Report results clearly
4. Take screenshots of important steps

Format your response:
- Start each action with [ACTION]
- Start each observation with [OBSERVE]
- Start each screenshot with [SCREENSHOT] followed by the file path
- End with [RESULT]: PASS or FAIL
- If failed, include [ERROR]: description"
```

### Output Parser

```python
def parse_claude_output(logs: str) -> ParsedResult:
    result = ParsedResult(success=False, screenshots=[], error=None)

    for line in logs.split('\n'):
        if line.startswith('[SCREENSHOT]'):
            screenshot_path = line.split('[SCREENSHOT]')[1].strip()
            result.screenshots.append(screenshot_path)
        elif line.startswith('[RESULT]'):
            result.success = 'PASS' in line
        elif line.startswith('[ERROR]'):
            result.error = line.split('[ERROR]')[1].strip()

    return result
```

### Executor Flow

```python
async def execute_web_test(test_id: uuid.UUID, websocket_manager: WebSocketManager):
    # 1. Update status to "running"
    # 2. Construct claude command
    # 3. Start subprocess with stdout/stderr capture
    # 4. Stream logs to WebSocket in real-time
    # 5. Parse output for screenshots, status
    # 6. Upload screenshots to MinIO
    # 7. Save result to database
    # 8. Push completion message via WebSocket
```

### WebSocket Manager

```python
class WebSocketManager:
    active_connections: dict[uuid.UUID, WebSocket] = {}

    async def connect(test_id: uuid.UUID, websocket: WebSocket)
    def disconnect(test_id: uuid.UUID)
    async def send_log(test_id: uuid.UUID, log: str)
    async def send_status(test_id: uuid.UUID, status: str)
    async def send_complete(test_id: uuid.UUID, result: dict)
```

## Error Handling

### Claude CLI Unavailable

```python
def check_claude_available() -> bool:
    try:
        subprocess.run(["claude", "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

# Pre-check on test creation
if not check_claude_available():
    raise HTTPException(503, "Claude CLI not installed")
```

### Test Timeout

- Default: 10 minutes (configurable via `WEB_TEST_TIMEOUT`)
- Process killed after timeout
- Status marked as "failed"

### WebSocket Disconnection

- Frontend: Auto-reconnect with exponential backoff (1s → 30s max)
- Backend: Execution continues, logs saved to database
- Max retry attempts: 10

### Concurrency Control

- Max concurrent tests: 3 (configurable via `MAX_CONCURRENT_TESTS`)
- Queue system when limit reached
- User notified of queue position

### URL Validation

```python
def validate_url(url: str) -> bool:
    result = urlparse(url)
    return all([result.scheme, result.netloc]) and result.scheme in ('http', 'https')

# Private network blocking (optional security measure)
FORBIDDEN_NETWORKS = ['127.0.0.0/8', '10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16']
```

### Test Cancellation

```python
# Users can cancel running tests
POST /api/web-tests/{id}/cancel
- Only owner can cancel
- Only "running" status can be cancelled
- Sends SIGTERM to subprocess
- Updates status to "cancelled"
```

### File Cleanup

- Automated cleanup of screenshots older than 30 days
- Admin endpoint for manual cleanup
- Removes both DB records and MinIO objects

## File Structure

### Backend Files

```
backend/app/
├── web_tests/
│   ├── __init__.py
│   ├── models.py      # WebTest, WebTestResult SQLModel
│   ├── crud.py        # CRUD operations
│   ├── api.py         # FastAPI routes
│   ├── executor.py    # Claude CLI execution logic
│   └── websocket.py   # WebSocket connection manager
├── api/
│   └── main.py        # Add web_tests router
└── core/
    └── minio.py       # Extend for screenshot storage
```

### Frontend Files

```
frontend/src/
├── components/
│   └── WebTests/
│       ├── TestList.tsx
│       ├── CreateTestForm.tsx
│       ├── TestDetail.tsx
│       ├── LogViewer.tsx
│       ├── StatusBadge.tsx
│       └── testColumns.tsx
├── hooks/
│   └── useWebSocketLog.ts
├── routes/
│   └── _layout/
│       └── web-tests.tsx
└── components/
    └── Sidebar/
        └── AppSidebar.tsx  # Add "Web Tests" menu item
```

### Database Migration

```
backend/app/alembic/versions/
└── XXXX_add_web_tests_tables.py  # New migration
```

## Implementation Notes

### Dependencies

**Backend:**
- `websockets` (if not already installed)
- MinIO client (already exists)

**Frontend:**
- No new dependencies (use existing WebSocket API)

### Configuration

Add to `.env`:
```bash
# Web Test Configuration
WEB_TEST_TIMEOUT=600  # 10 minutes
MAX_CONCURRENT_TESTS=3
MINIO_SCREENSHOTS_BUCKET=web-test-screenshots
```

### Security Considerations

1. All endpoints require authentication
2. WebSocket token validation
3. Ownership checks on all operations
4. URL validation to prevent SSRF attacks
5. Private network blocking (optional)
6. MinIO signed URLs with expiration

### Performance Considerations

1. Database indexes on `WebTest.owner_id`, `WebTest.status`, `WebTest.created_at`
2. WebSocket connection pooling
3. Async subprocess execution
4. Screenshot compression before storage

## Testing Strategy

### Unit Tests

- URL validation
- Output parser
- CRUD operations
- WebSocket manager

### Integration Tests

- API endpoints (create, read, delete, retry)
- WebSocket connection lifecycle
- Error scenarios (timeout, cancellation)

### E2E Tests

- Complete test creation flow
- Real Claude CLI execution (with mock or isolated environment)

## Future Enhancements

1. **Test Templates**: Predefined test scenarios (login form, navigation, etc.)
2. **Video Recording**: Option to record test execution video
3. **Comparison**: Compare results across multiple test runs
4. **Scheduling**: Run tests on a schedule (cron-like)
5. **Notifications**: Email/webhook notifications on completion
6. **Test Suites**: Group multiple tests into suites
7. **Export Results**: Export results as PDF or JSON
8. **Analytics**: Test success rate trends, performance metrics

## Rollout Plan

1. Phase 1: Core functionality (create, execute, view)
2. Phase 2: Management features (retry, delete, history)
3. Phase 3: Enhancements (templates, scheduling, analytics)

## Success Criteria

- Users can successfully create and execute web tests
- Real-time log streaming works reliably
- Test results are accurately captured and displayed
- System handles up to 3 concurrent tests without performance degradation
- Error scenarios are handled gracefully with clear user feedback
