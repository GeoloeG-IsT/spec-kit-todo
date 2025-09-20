import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState, useEffect } from 'react'
import { useAuth } from './useAuth'
import { apiClient } from '../api/client'
import {
  TodoItemResponse,
  TodoItemCreate,
  TodoItemUpdate,
  TodoItemReorder,
  TodoListResponse,
  BulkUpdateResponse,
  TodoListParams,
} from '../api/types'

// Query keys
const QUERY_KEYS = {
  todos: ['todos'] as const,
  todosList: (params?: TodoListParams) => ['todos', 'list', params] as const,
  todo: (id: string) => ['todos', id] as const,
}

export function useTodos(params?: TodoListParams) {
  const { getToken, isAuthenticated } = useAuth()
  const queryClient = useQueryClient()
  const [sessionId, setSessionId] = useState<string | null>(null)

  // Get or create session ID for guest users
  useEffect(() => {
    const getSessionId = async () => {
      const token = await getToken()
      if (!token) {
        // Guest user - get or create session
        let storedSessionId = localStorage.getItem('guest_session_id')
        if (!storedSessionId) {
          try {
            const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
            const sessionResponse = await fetch(`${baseUrl}/api/auth/session`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                user_agent: navigator.userAgent,
                ip_address: '', // Will be determined by backend
              }),
            })
            if (sessionResponse.ok) {
              const session = await sessionResponse.json()
              storedSessionId = session.id
              localStorage.setItem('guest_session_id', storedSessionId)
            }
          } catch (error) {
            console.error('Failed to create guest session:', error)
            // Generate fallback session ID
            storedSessionId = `guest_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
            localStorage.setItem('guest_session_id', storedSessionId)
          }
        }
        setSessionId(storedSessionId)
      }
    }

    getSessionId()
  }, [getToken])

  // Fetch todos query
  const {
    data: todosResponse,
    isLoading: loading,
    error,
    refetch,
  } = useQuery({
    queryKey: QUERY_KEYS.todosList(params),
    queryFn: async (): Promise<TodoListResponse> => {
      const token = await getToken()
      const queryParams = new URLSearchParams()

      if (params?.completed !== undefined) {
        queryParams.append('completed', params.completed.toString())
      }
      if (params?.priority) {
        queryParams.append('priority', params.priority)
      }
      if (params?.order_by) {
        queryParams.append('order_by', params.order_by)
      }
      if (params?.order_direction) {
        queryParams.append('order_direction', params.order_direction)
      }
      if (params?.limit) {
        queryParams.append('limit', params.limit.toString())
      }
      if (params?.offset) {
        queryParams.append('offset', params.offset.toString())
      }

      const url = `/api/todos${queryParams.toString() ? `?${queryParams.toString()}` : ''}`

      if (token) {
        return apiClient.get<TodoListResponse>(url, { token })
      } else if (sessionId) {
        return apiClient.get<TodoListResponse>(url, { sessionId })
      } else {
        // Return empty response for guests without session
        return { items: [], total: 0, limit: 50, offset: 0 }
      }
    },
    enabled: isAuthenticated || !!sessionId,
    staleTime: 30 * 1000, // 30 seconds
    refetchOnWindowFocus: true,
  })

  // Create todo mutation
  const createTodo = useMutation({
    mutationFn: async (todoData: TodoItemCreate): Promise<TodoItemResponse> => {
      const token = await getToken()

      if (token) {
        return apiClient.post<TodoItemResponse>('/api/todos', todoData, { token })
      } else if (sessionId) {
        return apiClient.post<TodoItemResponse>('/api/todos', todoData, { sessionId })
      } else {
        throw new Error('No authentication or session available')
      }
    },
    onSuccess: (newTodo) => {
      // Update the todos list cache
      queryClient.setQueryData(
        QUERY_KEYS.todosList(params),
        (old: TodoListResponse | undefined) => {
          if (!old) return { items: [newTodo], total: 1, limit: 50, offset: 0 }
          return {
            ...old,
            items: [newTodo, ...old.items],
            total: old.total + 1,
          }
        }
      )
      // Invalidate and refetch
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.todos })
    },
    onError: (error) => {
      console.error('Failed to create TODO:', error)
    },
  })

  // Update todo mutation
  const updateTodo = useMutation({
    mutationFn: async (updates: Partial<TodoItemResponse> & { id: string }): Promise<TodoItemResponse> => {
      const { id, ...updateData } = updates
      const token = await getToken()

      if (token) {
        return apiClient.put<TodoItemResponse>(`/api/todos/${id}`, updateData, { token })
      } else if (sessionId) {
        return apiClient.put<TodoItemResponse>(`/api/todos/${id}`, updateData, { sessionId })
      } else {
        throw new Error('No authentication or session available')
      }
    },
    onSuccess: (updatedTodo) => {
      // Update the todos list cache
      queryClient.setQueryData(
        QUERY_KEYS.todosList(params),
        (old: TodoListResponse | undefined) => {
          if (!old) return old
          return {
            ...old,
            items: old.items.map(todo =>
              todo.id === updatedTodo.id ? updatedTodo : todo
            ),
          }
        }
      )
      // Update individual todo cache
      queryClient.setQueryData(QUERY_KEYS.todo(updatedTodo.id), updatedTodo)
      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.todos })
    },
    onError: (error) => {
      console.error('Failed to update TODO:', error)
    },
  })

  // Delete todo mutation
  const deleteTodo = useMutation({
    mutationFn: async (id: string): Promise<void> => {
      const token = await getToken()

      if (token) {
        return apiClient.delete<void>(`/api/todos/${id}`, { token })
      } else if (sessionId) {
        return apiClient.delete<void>(`/api/todos/${id}`, { sessionId })
      } else {
        throw new Error('No authentication or session available')
      }
    },
    onSuccess: (_, deletedId) => {
      // Update the todos list cache
      queryClient.setQueryData(
        QUERY_KEYS.todosList(params),
        (old: TodoListResponse | undefined) => {
          if (!old) return old
          return {
            ...old,
            items: old.items.filter(todo => todo.id !== deletedId),
            total: old.total - 1,
          }
        }
      )
      // Remove individual todo from cache
      queryClient.removeQueries({ queryKey: QUERY_KEYS.todo(deletedId) })
      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.todos })
    },
    onError: (error) => {
      console.error('Failed to delete TODO:', error)
    },
  })

  // Reorder todos mutation
  const reorderTodos = useMutation({
    mutationFn: async (reorderData: TodoItemReorder): Promise<BulkUpdateResponse> => {
      const token = await getToken()

      if (token) {
        return apiClient.put<BulkUpdateResponse>('/api/todos/reorder', reorderData, { token })
      } else if (sessionId) {
        return apiClient.put<BulkUpdateResponse>('/api/todos/reorder', reorderData, { sessionId })
      } else {
        throw new Error('No authentication or session available')
      }
    },
    onSuccess: () => {
      // Invalidate and refetch todos to get the updated order
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.todos })
    },
    onError: (error) => {
      console.error('Failed to reorder TODOs:', error)
    },
  })

  // Bulk update todos mutation
  const bulkUpdateTodos = useMutation({
    mutationFn: async (bulkData: {
      todo_ids: string[]
      completed?: boolean
      priority?: string
    }): Promise<BulkUpdateResponse> => {
      const token = await getToken()

      if (token) {
        return apiClient.put<BulkUpdateResponse>('/api/todos/bulk', bulkData, { token })
      } else if (sessionId) {
        return apiClient.put<BulkUpdateResponse>('/api/todos/bulk', bulkData, { sessionId })
      } else {
        throw new Error('No authentication or session available')
      }
    },
    onSuccess: () => {
      // Invalidate and refetch todos to get the updated items
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.todos })
    },
    onError: (error) => {
      console.error('Failed to bulk update TODOs:', error)
    },
  })

  return {
    // Data
    todos: todosResponse?.items || [],
    totalTodos: todosResponse?.total || 0,
    loading,
    error,
    sessionId,

    // Actions
    createTodo,
    updateTodo,
    deleteTodo,
    reorderTodos,
    bulkUpdateTodos,
    refetch,

    // Utility functions
    invalidateTodos: () => queryClient.invalidateQueries({ queryKey: QUERY_KEYS.todos }),
    prefetchTodo: (id: string) => {
      return queryClient.prefetchQuery({
        queryKey: QUERY_KEYS.todo(id),
        queryFn: async () => {
          const token = await getToken()
          if (token) {
            return apiClient.get<TodoItemResponse>(`/api/todos/${id}`, { token })
          } else if (sessionId) {
            return apiClient.get<TodoItemResponse>(`/api/todos/${id}`, { sessionId })
          }
          throw new Error('No authentication or session available')
        },
        staleTime: 30 * 1000,
      })
    },
  }
}

// Hook for a single todo
export function useTodo(id: string) {
  const { getToken, isAuthenticated } = useAuth()

  return useQuery({
    queryKey: QUERY_KEYS.todo(id),
    queryFn: async (): Promise<TodoItemResponse> => {
      const token = await getToken()
      if (token) {
        return apiClient.get<TodoItemResponse>(`/api/todos/${id}`, { token })
      } else {
        // For guest users, we would need session ID here
        throw new Error('Authentication required for individual todo access')
      }
    },
    enabled: !!id && isAuthenticated,
    staleTime: 30 * 1000,
  })
}