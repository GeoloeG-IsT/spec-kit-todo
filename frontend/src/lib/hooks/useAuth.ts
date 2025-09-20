import { useAuth as useClerkAuth, useUser, useSignIn, useSignUp } from '@clerk/nextjs'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { useApiClient } from '../api/client'
import { UserResponse, UserCreate, SessionConvertResponse } from '../api/types'

export function useAuth() {
  const clerkAuth = useClerkAuth()
  const { user, isLoaded: userLoaded } = useUser()
  const { signIn, isLoaded: signInLoaded } = useSignIn()
  const { signUp, isLoaded: signUpLoaded } = useSignUp()
  const api = useApiClient()
  const queryClient = useQueryClient()

  const [isInitialized, setIsInitialized] = useState(false)

  // Initialize user in backend when authenticated
  const createOrUpdateUser = useMutation({
    mutationFn: async (userData: UserCreate): Promise<UserResponse> => {
      return api.post<UserResponse>('/api/auth/user', userData)
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
      return api.post<SessionConvertResponse>('/api/auth/convert-session', { session_id: sessionId })
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
      if (userLoaded && user && clerkAuth.isSignedIn && !isInitialized) {
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
  }, [userLoaded, user, clerkAuth.isSignedIn, isInitialized, createOrUpdateUser, convertGuestSession])

  // Sign out handler
  const handleSignOut = async () => {
    try {
      await clerkAuth.signOut()
      // Clear all caches
      queryClient.clear()
      setIsInitialized(false)
    } catch (error) {
      console.error('Failed to sign out:', error)
    }
  }

  // Auth state helpers
  const isAuthenticated = clerkAuth.isSignedIn
  const isLoading = !userLoaded || !signInLoaded || !signUpLoaded
  const isGuest = !isAuthenticated && userLoaded

  return {
    // Clerk auth state
    isAuthenticated,
    isGuest,
    isLoading,
    isInitialized,
    user,
    userId: user?.id,

    // Clerk methods
    signOut: handleSignOut,
    getToken: clerkAuth.getToken,

    // Clerk components props
    signIn,
    signUp,

    // Custom mutations
    createOrUpdateUser,
    convertGuestSession,

    // Utility methods
    getUserDisplayName: () => {
      if (!user) return 'Guest'
      return user.fullName || user.username || user.firstName || 'User'
    },

    getUserEmail: () => {
      return user?.primaryEmailAddress?.emailAddress || null
    },

    getUserAvatar: () => {
      return user?.imageUrl || null
    },

    getAuthProviders: () => {
      if (!user) return []
      return user.externalAccounts.map(account => ({
        provider: account.provider,
        email: account.emailAddress,
      }))
    },

    hasPassword: () => {
      return user?.passwordEnabled || false
    },

    // Session management
    refreshSession: async () => {
      try {
        await clerkAuth.session?.reload()
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
  const { user, isAuthenticated } = useAuth()
  const api = useApiClient()

  return {
    data: user,
    isLoading: !user && isAuthenticated,
    refetch: async () => {
      if (isAuthenticated) {
        try {
          const userData = await api.get<UserResponse>('/api/auth/user')
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