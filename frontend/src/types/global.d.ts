// Global type declarations

declare global {
  interface Window {
    // Add any global window properties here
    gtag?: (...args: any[]) => void
  }
}

// Declare modules for CSS imports
declare module '*.css' {
  const content: string
  export default content
}

declare module '*.scss' {
  const content: string
  export default content
}

// Declare modules for image imports
declare module '*.png'
declare module '*.jpg'
declare module '*.jpeg'
declare module '*.gif'
declare module '*.webp'
declare module '*.svg'

// Augment the Next.js environment variables
declare namespace NodeJS {
  interface ProcessEnv {
    NODE_ENV: 'development' | 'production' | 'test'
    NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY: string
    CLERK_SECRET_KEY: string
    NEXT_PUBLIC_CLERK_SIGN_IN_URL: string
    NEXT_PUBLIC_CLERK_SIGN_UP_URL: string
    NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL: string
    NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL: string
    NEXT_PUBLIC_API_URL: string
    NEXT_PUBLIC_APP_NAME: string
    NEXT_PUBLIC_APP_VERSION: string
    NEXT_PUBLIC_ENVIRONMENT: 'development' | 'staging' | 'production'
    NEXT_PUBLIC_ENABLE_REAL_TIME_SYNC: string
    NEXT_PUBLIC_ENABLE_ANALYTICS: string
    NEXT_PUBLIC_DEBUG: string
  }
}

export {}