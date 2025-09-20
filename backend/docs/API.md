# TODO API Documentation

## Base URL
```
Development: http://localhost:8000
Production: https://api.yourdomain.com
```

## Authentication

The API supports both guest sessions and authenticated users via Clerk.

### Headers

#### Guest Users
```http
X-Session-ID: <session-id>
```

#### Authenticated Users
```http
Authorization: Bearer <clerk-jwt-token>
```

## Endpoints

### Health Check

#### GET /health
Check API health status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-19T10:30:00Z"
}
```

---

### Session Management

#### POST /api/auth/session
Create a new guest session.

**Request:**
```json
{
  "user_agent": "Mozilla/5.0...",
  "ip_address": "192.168.1.1"
}
```

**Response:**
```json
{
  "id": "session_abc123",
  "created_at": "2025-01-19T10:30:00Z",
  "last_accessed_at": "2025-01-19T10:30:00Z"
}
```

#### POST /api/auth/session/convert
Convert guest session to user account.

**Headers:**
```http
Authorization: Bearer <clerk-jwt-token>
```

**Request:**
```json
{
  "session_id": "session_abc123"
}
```

**Response:**
```json
{
  "migrated_todos_count": 5,
  "session_id": "session_abc123",
  "user_id": "user_xyz789"
}
```

---

### User Management

#### POST /api/auth/user
Create or update user from Clerk data.

**Headers:**
```http
Authorization: Bearer <clerk-jwt-token>
```

**Request:**
```json
{
  "clerk_user_id": "user_abc123",
  "display_name": "John Doe",
  "email": "john@example.com",
  "avatar_url": "https://example.com/avatar.jpg"
}
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "clerk_user_id": "user_abc123",
  "display_name": "John Doe",
  "email": "john@example.com",
  "avatar_url": "https://example.com/avatar.jpg",
  "created_at": "2025-01-19T10:30:00Z",
  "last_login_at": "2025-01-19T10:30:00Z"
}
```

#### GET /api/auth/user/me
Get current user information.

**Headers:**
```http
Authorization: Bearer <clerk-jwt-token>
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "clerk_user_id": "user_abc123",
  "display_name": "John Doe",
  "email": "john@example.com",
  "created_at": "2025-01-19T10:30:00Z"
}
```

---

### TODO Operations

#### GET /api/todos
Get all TODOs for the current user/session.

**Query Parameters:**
- `completed` (boolean): Filter by completion status
- `priority` (string): Filter by priority (low, medium, high)
- `order_by` (string): Sort field (created_at, updated_at, priority, title, order_index)
- `order_direction` (string): Sort direction (asc, desc)
- `limit` (integer): Maximum items to return (default: 100)
- `offset` (integer): Number of items to skip (default: 0)

**Response:**
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "title": "Complete project documentation",
      "description": "Write comprehensive API docs",
      "completed": false,
      "completed_at": null,
      "priority": "high",
      "order_index": 0,
      "created_at": "2025-01-19T10:30:00Z",
      "updated_at": "2025-01-19T10:30:00Z"
    }
  ],
  "total": 1,
  "limit": 100,
  "offset": 0
}
```

#### POST /api/todos
Create a new TODO.

**Request:**
```json
{
  "title": "New TODO",
  "description": "Description of the task",
  "priority": "medium"
}
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440002",
  "title": "New TODO",
  "description": "Description of the task",
  "completed": false,
  "priority": "medium",
  "order_index": 1,
  "created_at": "2025-01-19T10:35:00Z",
  "updated_at": "2025-01-19T10:35:00Z"
}
```

#### PUT /api/todos/{todo_id}
Update a TODO.

**Request:**
```json
{
  "title": "Updated title",
  "description": "Updated description",
  "completed": true,
  "priority": "high"
}
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440002",
  "title": "Updated title",
  "description": "Updated description",
  "completed": true,
  "completed_at": "2025-01-19T10:40:00Z",
  "priority": "high",
  "order_index": 1,
  "created_at": "2025-01-19T10:35:00Z",
  "updated_at": "2025-01-19T10:40:00Z"
}
```

#### DELETE /api/todos/{todo_id}
Delete a TODO (soft delete).

**Response:**
```
204 No Content
```

#### POST /api/todos/bulk-update
Update multiple TODOs at once.

**Request:**
```json
{
  "todo_ids": ["id1", "id2", "id3"],
  "completed": true,
  "priority": "high"
}
```

**Response:**
```json
{
  "updated_count": 3
}
```

#### POST /api/todos/reorder
Reorder TODOs.

**Request:**
```json
{
  "todo_orders": [
    {"todo_id": "id1", "order_index": 0},
    {"todo_id": "id2", "order_index": 1},
    {"todo_id": "id3", "order_index": 2}
  ]
}
```

**Response:**
```json
{
  "reordered_count": 3
}
```

---

### Real-time Updates (SSE)

#### GET /api/todos/stream
Server-Sent Events stream for real-time TODO updates.

**Headers:**
```http
Accept: text/event-stream
X-Session-ID: <session-id> OR Authorization: Bearer <token>
```

**Event Types:**

```
event: todo_created
data: {"id": "...", "title": "...", "priority": "..."}

event: todo_updated
data: {"id": "...", "completed": true}

event: todo_deleted
data: {"id": "..."}

event: heartbeat
data: {"timestamp": "2025-01-19T10:30:00Z"}
```

---

## Error Responses

All endpoints return consistent error responses:

### 400 Bad Request
```json
{
  "error": "Invalid request",
  "detail": "Title is required"
}
```

### 401 Unauthorized
```json
{
  "error": "Unauthorized",
  "detail": "Invalid or expired token"
}
```

### 403 Forbidden
```json
{
  "error": "Forbidden",
  "detail": "You don't have permission to access this resource"
}
```

### 404 Not Found
```json
{
  "error": "Not found",
  "detail": "TODO with id 'xyz' not found"
}
```

### 429 Too Many Requests
```json
{
  "error": "Rate limit exceeded",
  "detail": "Please wait before making more requests"
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error",
  "detail": "An unexpected error occurred"
}
```

---

## Rate Limiting

- Guest sessions: 100 requests per minute
- Authenticated users: 300 requests per minute
- Bulk operations: 10 requests per minute

Rate limit headers are included in responses:
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1705665000
```

---

## CORS

The API supports CORS for the following origins:
- Development: `http://localhost:3000`
- Production: Configure via `CORS_ORIGINS` environment variable

---

## Pagination

List endpoints support pagination via `limit` and `offset` parameters:

```http
GET /api/todos?limit=20&offset=40
```

Response includes pagination metadata:
```json
{
  "items": [...],
  "total": 150,
  "limit": 20,
  "offset": 40
}
```

---

## Data Validation

### TODO Title
- Required
- Min length: 1
- Max length: 200

### TODO Description
- Optional
- Max length: 1000

### Priority
- Enum: `low`, `medium`, `high`
- Default: `medium`

### Order Index
- Integer
- Min: 0
- Auto-assigned if not provided