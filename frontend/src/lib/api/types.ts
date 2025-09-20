// API Types based on OpenAPI specification

export type TodoPriority = 'low' | 'medium' | 'high'

export type AuthProviderType = 'google' | 'github' | 'linkedin' | 'email'

// User types
export interface UserCreate {
  display_name: string
  clerk_user_id: string
}

export interface UserResponse {
  id: string
  clerk_user_id: string
  display_name: string
  email?: string
  avatar_url?: string
  created_at: string
  last_login_at?: string
}

// Session types
export interface SessionCreate {
  user_agent?: string
  ip_address?: string
}

export interface SessionResponse {
  id: string
  created_at: string
  last_accessed_at: string
}

// TODO types
export interface TodoItemCreate {
  title: string
  description?: string
  priority?: TodoPriority
}

export interface TodoItemUpdate {
  title?: string
  description?: string
  completed?: boolean
  priority?: TodoPriority
  order_index?: number
}

export interface TodoItemResponse {
  id: string
  title: string
  description?: string
  completed: boolean
  completed_at?: string
  priority: TodoPriority
  order_index: number
  created_at: string
  updated_at: string
}

export interface TodoItemBulkUpdate {
  todo_ids: string[]
  completed?: boolean
  priority?: TodoPriority
}

export interface TodoItemReorder {
  todo_orders: Array<{
    todo_id: string
    order_index: number
  }>
}

// List response types
export interface TodoListResponse {
  items: TodoItemResponse[]
  total: number
  limit: number
  offset: number
}

// Bulk operation responses
export interface BulkUpdateResponse {
  updated_count: number
}

export interface SessionConvertResponse {
  migrated_todos_count: number
}

// Auth Provider types
export interface AuthProviderResponse {
  provider: AuthProviderType
  email?: string
  created_at: string
  last_used_at: string
}

// SSE event types
export interface SSEEvent {
  event: 'todo_created' | 'todo_updated' | 'todo_deleted' | 'heartbeat'
  data: any
}

export interface TodoCreatedEvent {
  event: 'todo_created'
  data: TodoItemResponse
}

export interface TodoUpdatedEvent {
  event: 'todo_updated'
  data: Partial<TodoItemResponse> & { id: string }
}

export interface TodoDeletedEvent {
  event: 'todo_deleted'
  data: { id: string }
}

export interface HeartbeatEvent {
  event: 'heartbeat'
  data: { timestamp: string }
}

// Query parameters for TODO list
export interface TodoListParams {
  completed?: boolean
  priority?: TodoPriority
  order_by?: 'created_at' | 'updated_at' | 'priority' | 'title' | 'order_index'
  order_direction?: 'asc' | 'desc'
  limit?: number
  offset?: number
}