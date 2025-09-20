import { useEffect, useRef, useState, useCallback } from 'react'
import { useAuth } from '@clerk/nextjs'
import { useQueryClient } from '@tanstack/react-query'
import {
  TodoItemResponse,
  SSEEvent,
  TodoCreatedEvent,
  TodoUpdatedEvent,
  TodoDeletedEvent,
  HeartbeatEvent,
  TodoListResponse,
} from '../api/types'

interface UseRealTimeSyncOptions {
  enabled?: boolean
  reconnectInterval?: number
  maxReconnectAttempts?: number
  heartbeatTimeout?: number
}

interface ConnectionStatus {
  isConnected: boolean
  isConnecting: boolean
  lastConnected: Date | null
  reconnectAttempts: number
  error: string | null
}

export function useRealTimeSync(options: UseRealTimeSyncOptions = {}) {
  const {
    enabled = true,
    reconnectInterval = 3000,
    maxReconnectAttempts = 5,
    heartbeatTimeout = 30000,
  } = options

  const { getToken, isSignedIn } = useAuth()
  const queryClient = useQueryClient()

  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>({
    isConnected: false,
    isConnecting: false,
    lastConnected: null,
    reconnectAttempts: 0,
    error: null,
  })

  const eventSourceRef = useRef<EventSource | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const heartbeatTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const reconnectAttemptsRef = useRef(0)

  // Handle incoming SSE events
  const handleSSEEvent = useCallback((event: MessageEvent) => {
    try {
      const eventData: SSEEvent = {
        event: event.type as any,
        data: JSON.parse(event.data),
      }

      switch (eventData.event) {
        case 'todo_created':
          handleTodoCreated(eventData as TodoCreatedEvent)
          break
        case 'todo_updated':
          handleTodoUpdated(eventData as TodoUpdatedEvent)
          break
        case 'todo_deleted':
          handleTodoDeleted(eventData as TodoDeletedEvent)
          break
        case 'heartbeat':
          handleHeartbeat(eventData as HeartbeatEvent)
          break
        default:
          console.log('Unknown SSE event:', eventData)
      }
    } catch (error) {
      console.error('Failed to parse SSE event:', error)
    }
  }, [])

  // Handle todo created event
  const handleTodoCreated = useCallback((event: TodoCreatedEvent) => {
    const newTodo = event.data

    // Update todos list cache
    queryClient.setQueryData(
      ['todos', 'list'],
      (old: TodoListResponse | undefined) => {
        if (!old) return old

        // Check if todo already exists (avoid duplicates)
        const exists = old.items.some(todo => todo.id === newTodo.id)
        if (exists) return old

        return {
          ...old,
          items: [newTodo, ...old.items],
          total: old.total + 1,
        }
      }
    )

    // Add to individual todo cache
    queryClient.setQueryData(['todos', newTodo.id], newTodo)

    console.log('Todo created via SSE:', newTodo.title)
  }, [queryClient])

  // Handle todo updated event
  const handleTodoUpdated = useCallback((event: TodoUpdatedEvent) => {
    const updates = event.data

    // Update todos list cache
    queryClient.setQueryData(
      ['todos', 'list'],
      (old: TodoListResponse | undefined) => {
        if (!old) return old

        return {
          ...old,
          items: old.items.map(todo =>
            todo.id === updates.id ? { ...todo, ...updates } : todo
          ),
        }
      }
    )

    // Update individual todo cache
    queryClient.setQueryData(
      ['todos', updates.id],
      (old: TodoItemResponse | undefined) => {
        if (!old) return old
        return { ...old, ...updates }
      }
    )

    console.log('Todo updated via SSE:', updates.id)
  }, [queryClient])

  // Handle todo deleted event
  const handleTodoDeleted = useCallback((event: TodoDeletedEvent) => {
    const { id } = event.data

    // Update todos list cache
    queryClient.setQueryData(
      ['todos', 'list'],
      (old: TodoListResponse | undefined) => {
        if (!old) return old

        return {
          ...old,
          items: old.items.filter(todo => todo.id !== id),
          total: old.total - 1,
        }
      }
    )

    // Remove from individual todo cache
    queryClient.removeQueries({ queryKey: ['todos', id] })

    console.log('Todo deleted via SSE:', id)
  }, [queryClient])

  // Handle heartbeat event
  const handleHeartbeat = useCallback((event: HeartbeatEvent) => {
    // Reset heartbeat timeout
    if (heartbeatTimeoutRef.current) {
      clearTimeout(heartbeatTimeoutRef.current)
    }

    heartbeatTimeoutRef.current = setTimeout(() => {
      console.warn('SSE heartbeat timeout, connection may be lost')
      setConnectionStatus(prev => ({
        ...prev,
        error: 'Connection timeout',
        isConnected: false,
      }))
    }, heartbeatTimeout)

    console.log('SSE heartbeat received:', event.data.timestamp)
  }, [heartbeatTimeout])

  // Create SSE connection
  const connect = useCallback(async () => {
    if (!enabled || !isSignedIn || eventSourceRef.current) {
      return
    }

    try {
      setConnectionStatus(prev => ({ ...prev, isConnecting: true, error: null }))

      const token = await getToken()
      if (!token) {
        throw new Error('No authentication token available')
      }

      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const url = `${baseUrl}/api/todos/stream`

      const eventSource = new EventSource(url, {
        withCredentials: true,
      })

      // Add Authorization header manually (EventSource doesn't support custom headers)
      // We'll need to pass the token as a query parameter or use a different approach
      const urlWithAuth = `${url}?token=${encodeURIComponent(token)}`
      const authenticatedEventSource = new EventSource(urlWithAuth)

      authenticatedEventSource.onopen = () => {
        console.log('SSE connection opened')
        setConnectionStatus({
          isConnected: true,
          isConnecting: false,
          lastConnected: new Date(),
          reconnectAttempts: 0,
          error: null,
        })
        reconnectAttemptsRef.current = 0
      }

      authenticatedEventSource.onerror = (error) => {
        console.error('SSE connection error:', error)
        setConnectionStatus(prev => ({
          ...prev,
          isConnected: false,
          isConnecting: false,
          error: 'Connection failed',
        }))

        // Schedule reconnect
        if (reconnectAttemptsRef.current < maxReconnectAttempts) {
          scheduleReconnect()
        } else {
          console.error('Max reconnect attempts reached')
          setConnectionStatus(prev => ({
            ...prev,
            error: 'Max reconnect attempts reached',
          }))
        }
      }

      // Add event listeners for each event type
      authenticatedEventSource.addEventListener('todo_created', handleSSEEvent)
      authenticatedEventSource.addEventListener('todo_updated', handleSSEEvent)
      authenticatedEventSource.addEventListener('todo_deleted', handleSSEEvent)
      authenticatedEventSource.addEventListener('heartbeat', handleSSEEvent)

      // Generic message handler for other events
      authenticatedEventSource.onmessage = handleSSEEvent

      eventSourceRef.current = authenticatedEventSource

    } catch (error) {
      console.error('Failed to create SSE connection:', error)
      setConnectionStatus(prev => ({
        ...prev,
        isConnecting: false,
        error: error instanceof Error ? error.message : 'Connection failed',
      }))
      scheduleReconnect()
    }
  }, [enabled, isSignedIn, getToken, maxReconnectAttempts, handleSSEEvent])

  // Schedule reconnection
  const scheduleReconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
    }

    reconnectAttemptsRef.current += 1
    setConnectionStatus(prev => ({
      ...prev,
      reconnectAttempts: reconnectAttemptsRef.current,
    }))

    const delay = reconnectInterval * Math.pow(2, reconnectAttemptsRef.current - 1) // Exponential backoff
    console.log(`Scheduling SSE reconnect in ${delay}ms (attempt ${reconnectAttemptsRef.current})`)

    reconnectTimeoutRef.current = setTimeout(() => {
      disconnect()
      connect()
    }, delay)
  }, [reconnectInterval, connect])

  // Disconnect SSE connection
  const disconnect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
      eventSourceRef.current = null
    }

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }

    if (heartbeatTimeoutRef.current) {
      clearTimeout(heartbeatTimeoutRef.current)
      heartbeatTimeoutRef.current = null
    }

    setConnectionStatus(prev => ({
      ...prev,
      isConnected: false,
      isConnecting: false,
    }))
  }, [])

  // Manual reconnect
  const reconnect = useCallback(() => {
    reconnectAttemptsRef.current = 0
    disconnect()
    connect()
  }, [connect, disconnect])

  // Initialize connection
  useEffect(() => {
    if (enabled && isSignedIn) {
      connect()
    }

    return () => {
      disconnect()
    }
  }, [enabled, isSignedIn, connect, disconnect])

  // Handle visibility change (reconnect when tab becomes visible)
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible' && enabled && isSignedIn) {
        if (!connectionStatus.isConnected && !connectionStatus.isConnecting) {
          reconnect()
        }
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange)
    }
  }, [enabled, isSignedIn, connectionStatus.isConnected, connectionStatus.isConnecting, reconnect])

  // Handle online/offline events
  useEffect(() => {
    const handleOnline = () => {
      if (enabled && isSignedIn) {
        reconnect()
      }
    }

    const handleOffline = () => {
      disconnect()
    }

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [enabled, isSignedIn, reconnect, disconnect])

  return {
    // Connection state
    ...connectionStatus,

    // Control methods
    connect,
    disconnect,
    reconnect,

    // Configuration
    isEnabled: enabled,
    maxReconnectAttempts,
    reconnectInterval,
  }
}