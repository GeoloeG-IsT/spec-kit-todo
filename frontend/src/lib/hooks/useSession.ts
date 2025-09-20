import { useState, useEffect, useCallback } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useAuth } from './useAuth'
import { SessionResponse, SessionCreate } from '../api/types'
import { apiClient } from '../api/client'

interface SessionState {
  sessionId: string | null
  isGuest: boolean
  isLoading: boolean
  error: string | null
  createdAt: Date | null
  lastAccessedAt: Date | null
}

const SESSION_STORAGE_KEY = 'guest_session_id'
const SESSION_METADATA_KEY = 'guest_session_metadata'

export function useSession() {
  const { isAuthenticated, getToken } = useAuth()
  const queryClient = useQueryClient()

  const [sessionState, setSessionState] = useState<SessionState>({
    sessionId: null,
    isGuest: false,
    isLoading: true,
    error: null,
    createdAt: null,
    lastAccessedAt: null,
  })

  // Create guest session mutation
  const createGuestSession = useMutation({
    mutationFn: async (sessionData: SessionCreate): Promise<SessionResponse> => {
      return apiClient.post<SessionResponse>('/api/auth/session', sessionData)
    },
    onSuccess: (sessionResponse) => {
      // Store session ID and metadata
      localStorage.setItem(SESSION_STORAGE_KEY, sessionResponse.id)
      localStorage.setItem(SESSION_METADATA_KEY, JSON.stringify({
        id: sessionResponse.id,
        createdAt: sessionResponse.created_at,
        lastAccessedAt: sessionResponse.last_accessed_at,
      }))

      setSessionState(prev => ({
        ...prev,
        sessionId: sessionResponse.id,
        isGuest: true,
        isLoading: false,
        error: null,
        createdAt: new Date(sessionResponse.created_at),
        lastAccessedAt: new Date(sessionResponse.last_accessed_at),
      }))

      console.log('Guest session created:', sessionResponse.id)
    },
    onError: (error) => {
      console.error('Failed to create guest session:', error)
      // Create fallback local session
      const fallbackSessionId = createFallbackSession()
      setSessionState(prev => ({
        ...prev,
        sessionId: fallbackSessionId,
        isGuest: true,
        isLoading: false,
        error: 'Failed to create server session, using local session',
        createdAt: new Date(),
        lastAccessedAt: new Date(),
      }))
    },
  })

  // Get session info query (for authenticated users checking if they have a guest session to convert)
  const sessionQuery = useQuery({
    queryKey: ['session', sessionState.sessionId],
    queryFn: async (): Promise<SessionResponse | null> => {
      if (!sessionState.sessionId) return null

      try {
        return await apiClient.get<SessionResponse>(`/api/auth/session/${sessionState.sessionId}`)
      } catch (error) {
        console.error('Failed to fetch session info:', error)
        return null
      }
    },
    enabled: !!sessionState.sessionId && !isAuthenticated,
    staleTime: 5 * 60 * 1000, // 5 minutes
  })

  // Create fallback session for offline or error scenarios
  const createFallbackSession = useCallback((): string => {
    const fallbackId = `local_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    localStorage.setItem(SESSION_STORAGE_KEY, fallbackId)
    localStorage.setItem(SESSION_METADATA_KEY, JSON.stringify({
      id: fallbackId,
      createdAt: new Date().toISOString(),
      lastAccessedAt: new Date().toISOString(),
      isLocal: true,
    }))
    return fallbackId
  }, [])

  // Initialize session
  const initializeSession = useCallback(async () => {
    // If user is signed in, they don't need a guest session
    if (isAuthenticated) {
      setSessionState(prev => ({
        ...prev,
        sessionId: null,
        isGuest: false,
        isLoading: false,
        error: null,
      }))
      return
    }

    setSessionState(prev => ({ ...prev, isLoading: true }))

    // Check for existing session
    const storedSessionId = localStorage.getItem(SESSION_STORAGE_KEY)
    const storedMetadata = localStorage.getItem(SESSION_METADATA_KEY)

    if (storedSessionId && storedMetadata) {
      try {
        const metadata = JSON.parse(storedMetadata)
        setSessionState(prev => ({
          ...prev,
          sessionId: storedSessionId,
          isGuest: true,
          isLoading: false,
          error: null,
          createdAt: new Date(metadata.createdAt),
          lastAccessedAt: new Date(metadata.lastAccessedAt),
        }))
        return
      } catch (error) {
        console.error('Failed to parse session metadata:', error)
      }
    }

    // Create new guest session
    try {
      await createGuestSession.mutateAsync({
        user_agent: navigator.userAgent,
        ip_address: '', // Will be determined by backend
      })
    } catch (error) {
      console.error('Session initialization failed:', error)
    }
  }, [isAuthenticated, createGuestSession])

  // Clear session
  const clearSession = useCallback(() => {
    localStorage.removeItem(SESSION_STORAGE_KEY)
    localStorage.removeItem(SESSION_METADATA_KEY)
    setSessionState({
      sessionId: null,
      isGuest: false,
      isLoading: false,
      error: null,
      createdAt: null,
      lastAccessedAt: null,
    })
    // Clear todos cache since they were associated with the session
    queryClient.invalidateQueries({ queryKey: ['todos'] })
  }, [queryClient])

  // Update last accessed time
  const updateLastAccessed = useCallback(() => {
    if (sessionState.sessionId && sessionState.isGuest) {
      const now = new Date()
      setSessionState(prev => ({
        ...prev,
        lastAccessedAt: now,
      }))

      // Update stored metadata
      const storedMetadata = localStorage.getItem(SESSION_METADATA_KEY)
      if (storedMetadata) {
        try {
          const metadata = JSON.parse(storedMetadata)
          metadata.lastAccessedAt = now.toISOString()
          localStorage.setItem(SESSION_METADATA_KEY, JSON.stringify(metadata))
        } catch (error) {
          console.error('Failed to update session metadata:', error)
        }
      }
    }
  }, [sessionState.sessionId, sessionState.isGuest])

  // Check if session has expired (optional, for future use)
  const isSessionExpired = useCallback((): boolean => {
    if (!sessionState.lastAccessedAt) return false

    // Sessions expire after 30 days of inactivity
    const expiryTime = 30 * 24 * 60 * 60 * 1000 // 30 days in milliseconds
    const timeSinceLastAccess = Date.now() - sessionState.lastAccessedAt.getTime()

    return timeSinceLastAccess > expiryTime
  }, [sessionState.lastAccessedAt])

  // Get session duration
  const getSessionDuration = useCallback((): number | null => {
    if (!sessionState.createdAt) return null
    return Date.now() - sessionState.createdAt.getTime()
  }, [sessionState.createdAt])

  // Initialize session on mount and auth state changes
  useEffect(() => {
    initializeSession()
  }, [initializeSession])

  // Update last accessed time periodically
  useEffect(() => {
    if (sessionState.isGuest && sessionState.sessionId) {
      updateLastAccessed()

      const interval = setInterval(updateLastAccessed, 5 * 60 * 1000) // Update every 5 minutes
      return () => clearInterval(interval)
    }
  }, [sessionState.isGuest, sessionState.sessionId, updateLastAccessed])

  // Handle page visibility changes
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible' && sessionState.isGuest) {
        updateLastAccessed()
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange)
    }
  }, [sessionState.isGuest, updateLastAccessed])

  // Clean up expired sessions
  useEffect(() => {
    if (sessionState.isGuest && isSessionExpired()) {
      console.log('Guest session expired, clearing...')
      clearSession()
    }
  }, [sessionState.isGuest, isSessionExpired, clearSession])

  return {
    // Session state
    sessionId: sessionState.sessionId,
    isGuest: sessionState.isGuest,
    isLoading: sessionState.isLoading,
    error: sessionState.error,
    createdAt: sessionState.createdAt,
    lastAccessedAt: sessionState.lastAccessedAt,

    // Session info from server
    sessionInfo: sessionQuery.data,

    // Actions
    clearSession,
    updateLastAccessed,
    refreshSession: initializeSession,

    // Utilities
    isSessionExpired: isSessionExpired(),
    sessionDuration: getSessionDuration(),
    hasValidSession: !!sessionState.sessionId && !isSessionExpired(),

    // Mutation states
    isCreatingSession: createGuestSession.isPending,
    sessionCreationError: createGuestSession.error,

    // For debugging
    sessionMetadata: sessionState,
  }
}

// Hook for session statistics and management
export function useSessionStats() {
  const { sessionId, createdAt, sessionDuration, isGuest } = useSession()

  const formatSessionDuration = useCallback((duration: number | null): string => {
    if (!duration) return 'Unknown'

    const seconds = Math.floor(duration / 1000)
    const minutes = Math.floor(seconds / 60)
    const hours = Math.floor(minutes / 60)
    const days = Math.floor(hours / 24)

    if (days > 0) return `${days}d ${hours % 24}h ${minutes % 60}m`
    if (hours > 0) return `${hours}h ${minutes % 60}m`
    if (minutes > 0) return `${minutes}m ${seconds % 60}s`
    return `${seconds}s`
  }, [])

  const getSessionAge = useCallback((): string => {
    if (!createdAt) return 'Unknown'

    const age = Date.now() - createdAt.getTime()
    return formatSessionDuration(age)
  }, [createdAt, formatSessionDuration])

  return {
    sessionId: sessionId?.slice(0, 8), // First 8 characters for display
    sessionAge: getSessionAge(),
    sessionDuration: formatSessionDuration(sessionDuration),
    isActiveSession: isGuest && !!sessionId,
    createdAt,
  }
}