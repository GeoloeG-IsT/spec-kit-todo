'use client'

import { ClerkProvider } from '@clerk/nextjs'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { useState } from 'react'

interface ProvidersProps {
  children: React.ReactNode
}

export function Providers({ children }: ProvidersProps) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000, // 1 minute
            gcTime: 10 * 60 * 1000, // 10 minutes
            retry: (failureCount, error: any) => {
              // Don't retry on 4xx errors
              if (error?.status >= 400 && error?.status < 500) {
                return false
              }
              return failureCount < 3
            },
          },
          mutations: {
            retry: (failureCount, error: any) => {
              // Don't retry on 4xx errors
              if (error?.status >= 400 && error?.status < 500) {
                return false
              }
              return failureCount < 2
            },
          },
        },
      })
  )

  return (
    <ClerkProvider
      appearance={{
        baseTheme: undefined,
        variables: {
          colorPrimary: '#00FFFF', // Cyberpunk cyan
          colorDanger: '#FF00FF', // Cyberpunk magenta
          colorSuccess: '#00FF00', // Cyberpunk green
          colorWarning: '#FFFF00', // Cyberpunk yellow
          colorText: '#00FFFF',
          colorTextSecondary: '#8A2BE2',
          colorBackground: '#0A0A0A',
          colorInputBackground: '#1A1A1A',
          colorInputText: '#00FFFF',
          borderRadius: '0.375rem',
          fontFamily: `var(--font-jetbrains-mono), monospace`,
        },
        elements: {
          formButtonPrimary: {
            backgroundColor: '#00FFFF',
            color: '#000000',
            '&:hover': {
              backgroundColor: '#00CCCC',
              textShadow: '0 0 10px #00FFFF',
            },
          },
          card: {
            backgroundColor: '#1A1A1A',
            border: '1px solid #00FFFF',
            boxShadow: '0 0 20px rgba(0, 255, 255, 0.3)',
          },
          headerTitle: {
            color: '#00FFFF',
            fontFamily: `var(--font-jetbrains-mono), monospace`,
          },
          headerSubtitle: {
            color: '#8A2BE2',
          },
        },
      }}
      publishableKey={process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY}
      signInUrl="/sign-in"
      signUpUrl="/sign-up"
      afterSignInUrl="/"
      afterSignUpUrl="/"
    >
      <QueryClientProvider client={queryClient}>
        {children}
        <ReactQueryDevtools initialIsOpen={false} />
      </QueryClientProvider>
    </ClerkProvider>
  )
}