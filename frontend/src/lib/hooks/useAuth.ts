import { useAuth as useClerkAuth, useUser, useSignIn, useSignUp } from '@clerk/nextjs'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useEffect, useState, useCallback } from 'react'
import { apiClient } from '../api/client'
import { UserResponse, UserCreate, SessionConvertResponse } from '../api/types'
import { useDevMode } from '../../app/providers'

export function useAuth() {
  const { isDevMode, mockUser } = useDevMode()

  // Always call Clerk hooks to avoid breaking Rules of Hooks, but ignore them in dev mode
  let clerkAuth
  let user
  let userLoaded
  let signIn
  let signInLoaded
  let signUp
  let signUpLoaded

  try {
    clerkAuth = useClerkAuth()
    const clerkUser = useUser()
    user = clerkUser.user
    userLoaded = clerkUser.isLoaded
    const clerkSignIn = useSignIn()
    signIn = clerkSignIn.signIn
    signInLoaded = clerkSignIn.isLoaded
    const clerkSignUp = useSignUp()
    signUp = clerkSignUp.signUp
    signUpLoaded = clerkSignUp.isLoaded
  } catch (error) {
    // If Clerk context is not available (dev mode), use defaults
    clerkAuth = null
    user = null
    userLoaded = true
    signIn = null
    signInLoaded = true
    signUp = null
    signUpLoaded = true
  }

  const queryClient = useQueryClient()

  const [isInitialized, setIsInitialized] = useState(isDevMode) // Auto-initialize in dev mode

  // Initialize user in backend when authenticated
  const createOrUpdateUser = useMutation({
    mutationFn: async (userData: UserCreate): Promise<UserResponse> => {
      const token = isDevMode ? null : (clerkAuth ? await clerkAuth.getToken() : null)
      return apiClient.post<UserResponse>('/api/auth/user', userData, token ? { token } : {})
    },
    onSuccess: (userData) => {
      // Cache user data
      queryClient.setQueryData(['user', 'profile'], userData)
    },
    onError: (error) => {
      console.error('Failed to create/update user:', error)
    },
  })

  // Convert guest session to user account
  const convertGuestSession = useMutation({
    mutationFn: async (sessionId: string): Promise<SessionConvertResponse> => {
      const token = isDevMode ? null : (clerkAuth ? await clerkAuth.getToken() : null)
      return apiClient.post<SessionConvertResponse>('/api/auth/convert-session', { session_id: sessionId }, token ? { token } : {})
    },
    onSuccess: (result) => {
      // Clear guest session from localStorage
      localStorage.removeItem('guest_session_id')
      // Invalidate todos cache to refetch with user account
      queryClient.invalidateQueries({ queryKey: ['todos'] })
      console.log(`Converted guest session, migrated ${result.migrated_todos_count} TODOs`)
    },
    onError: (error) => {
      console.error('Failed to convert guest session:', error)
    },
  })

  // Initialize user when authenticated
  useEffect(() => {
    const initializeUser = async () => {
      if (isDevMode) {
        // In dev mode, we're already initialized with mock user
        setIsInitialized(true)
        return
      }

      if (userLoaded && user && clerkAuth?.isSignedIn && !isInitialized) {
        try {
          const userData: UserCreate = {
            clerk_user_id: user.id,
            display_name: user.fullName || user.username || 'User',
          }

          await createOrUpdateUser.mutateAsync(userData)

          // Check if there's a guest session to convert
          const guestSessionId = localStorage.getItem('guest_session_id')
          if (guestSessionId) {
            await convertGuestSession.mutateAsync(guestSessionId)
          }

          setIsInitialized(true)
        } catch (error) {
          console.error('Failed to initialize user:', error)
        }
      }
    }

    initializeUser()
  }, [isDevMode, userLoaded, user, clerkAuth?.isSignedIn, isInitialized, createOrUpdateUser, convertGuestSession])

  // Sign out handler
  const handleSignOut = useCallback(async () => {
    try {
      if (!isDevMode && clerkAuth) {
        await clerkAuth.signOut()
      }
      // Clear all caches
      queryClient.clear()
      setIsInitialized(isDevMode) // Reset to dev mode state
    } catch (error) {
      console.error('Failed to sign out:', error)
    }
  }, [isDevMode, clerkAuth, queryClient])

  // Memoize getToken function to prevent infinite re-renders
  const getToken = useCallback(async (): Promise<string | null> => {
    if (isDevMode) return null
    if (clerkAuth?.getToken) {
      return await clerkAuth.getToken()
    }
    return null
  }, [isDevMode, clerkAuth])

  // Auth state helpers
  const isAuthenticated = isDevMode ? true : (clerkAuth?.isSignedIn || false)
  const isLoading = isDevMode ? false : (!userLoaded || !signInLoaded || !signUpLoaded)
  const isGuest = isDevMode ? false : (!isAuthenticated && userLoaded)

  return {
    // Clerk auth state
    isAuthenticated,
    isGuest,
    isLoading,
    isInitialized,
    user: isDevMode ? mockUser : user,
    userId: isDevMode ? mockUser?.id : user?.id,

    // Clerk methods
    signOut: handleSignOut,
    getToken,

    // Clerk components props
    signIn,
    signUp,

    // Custom mutations
    createOrUpdateUser,
    convertGuestSession,

    // Utility methods
    getUserDisplayName: () => {
      if (isDevMode) return 'Dev User'
      if (!user) return 'Guest'
      return user.fullName || user.username || user.firstName || 'User'
    },

    getUserEmail: () => {
      if (isDevMode) return mockUser?.email || 'dev@example.com'
      return user?.primaryEmailAddress?.emailAddress || null
    },

    getUserAvatar: () => {
      if (isDevMode) return null
      return user?.imageUrl || null
    },

    getAuthProviders: () => {
      if (isDevMode) return [{ provider: 'dev', email: mockUser?.email || 'dev@example.com' }]
      if (!user) return []
      return user.externalAccounts.map(account => ({
        provider: account.provider,
        email: account.emailAddress,
      }))
    },

    hasPassword: () => {
      if (isDevMode) return true
      return user?.passwordEnabled || false
    },

    // Session management
    refreshSession: async () => {
      try {
        if (!isDevMode && clerkAuth?.session) {
          await clerkAuth.session.reload()
        }
        // Refresh user data in backend
        if (user) {
          const userData: UserCreate = {
            clerk_user_id: user.id,
            display_name: user.fullName || user.username || 'User',
          }
          await createOrUpdateUser.mutateAsync(userData)
        }
      } catch (error) {
        console.error('Failed to refresh session:', error)
      }
    },

    // Guest session utilities
    hasGuestSession: () => {
      return !!localStorage.getItem('guest_session_id')
    },

    clearGuestSession: () => {
      localStorage.removeItem('guest_session_id')
      queryClient.invalidateQueries({ queryKey: ['todos'] })
    },

    // Error states
    authError: createOrUpdateUser.error || convertGuestSession.error,
    isAuthenticating: createOrUpdateUser.isPending,
    isConvertingSession: convertGuestSession.isPending,
  }
}

// Hook for getting user profile data
export function useUserProfile() {
  const { user, isAuthenticated, getToken } = useAuth()

  return {
    data: user,
    isLoading: !user && isAuthenticated,
    refetch: async () => {
      if (isAuthenticated) {
        try {
          const token = await getToken()
          const userData = await apiClient.get<UserResponse>('/api/auth/user', token ? { token } : {})
          return userData
        } catch (error) {
          console.error('Failed to fetch user profile:', error)
          return null
        }
      }
      return null
    },
  }
}

// Hook for authentication status with loading states
export function useAuthStatus() {
  const { isAuthenticated, isGuest, isLoading, isInitialized } = useAuth()

  return {
    isAuthenticated,
    isGuest,
    isLoading: isLoading || (isAuthenticated && !isInitialized),
    isReady: !isLoading && (isAuthenticated ? isInitialized : true),
  }
}