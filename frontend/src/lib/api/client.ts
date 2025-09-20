// Import will be done dynamically to avoid circular dependencies

export interface ApiError {
  error: string
  message: string
  details?: Record<string, any>
}

export class HttpError extends Error {
  constructor(
    public status: number,
    public error: string,
    message: string,
    public details?: Record<string, any>
  ) {
    super(message)
    this.name = 'HttpError'
  }
}

export interface ApiClientConfig {
  baseUrl?: string
  timeout?: number
}

export class ApiClient {
  private baseUrl: string
  private timeout: number

  constructor(config: ApiClientConfig = {}) {
    this.baseUrl = config.baseUrl || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    this.timeout = config.timeout || 10000
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit & { token?: string; sessionId?: string } = {}
  ): Promise<T> {
    const { token, sessionId, ...requestOptions } = options

    const url = `${this.baseUrl}${endpoint}`
    const headers = new Headers(requestOptions.headers)

    // Set content type for non-GET requests with body
    if (requestOptions.method !== 'GET' && requestOptions.body) {
      headers.set('Content-Type', 'application/json')
    }

    // Add authentication headers
    if (token) {
      headers.set('Authorization', `Bearer ${token}`)
    } else if (sessionId) {
      headers.set('X-Session-ID', sessionId)
    }

    // Create abort controller for timeout
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), this.timeout)

    try {
      const response = await fetch(url, {
        ...requestOptions,
        headers,
        signal: controller.signal,
      })

      clearTimeout(timeoutId)

      if (!response.ok) {
        let errorData: ApiError
        try {
          errorData = await response.json()
        } catch {
          errorData = {
            error: 'unknown_error',
            message: `HTTP ${response.status}: ${response.statusText}`,
          }
        }

        throw new HttpError(
          response.status,
          errorData.error,
          errorData.message,
          errorData.details
        )
      }

      // Handle empty responses (204 No Content)
      if (response.status === 204) {
        return undefined as T
      }

      const contentType = response.headers.get('content-type')
      if (contentType?.includes('application/json')) {
        return response.json()
      }

      return response.text() as T
    } catch (error) {
      clearTimeout(timeoutId)

      if (error instanceof HttpError) {
        throw error
      }

      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          throw new HttpError(408, 'timeout', 'Request timeout')
        }
        throw new HttpError(0, 'network_error', error.message)
      }

      throw new HttpError(0, 'unknown_error', 'An unknown error occurred')
    }
  }

  async get<T>(endpoint: string, options?: RequestInit & { token?: string; sessionId?: string }): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: 'GET' })
  }

  async post<T>(
    endpoint: string,
    data?: any,
    options?: RequestInit & { token?: string; sessionId?: string }
  ): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  async put<T>(
    endpoint: string,
    data?: any,
    options?: RequestInit & { token?: string; sessionId?: string }
  ): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  async delete<T>(endpoint: string, options?: RequestInit & { token?: string; sessionId?: string }): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: 'DELETE' })
  }
}

// Hook to create authenticated API client
// Note: To avoid circular imports, this hook doesn't automatically get auth tokens
// Consumers should pass tokens explicitly or use the apiClient directly
export function useApiClient() {
  const client = new ApiClient()

  const request = async <T>(
    method: 'GET' | 'POST' | 'PUT' | 'DELETE',
    endpoint: string,
    data?: any,
    token?: string | null
  ): Promise<T> => {
    switch (method) {
      case 'GET':
        return client.get<T>(endpoint, token ? { token } : {})
      case 'POST':
        return client.post<T>(endpoint, data, token ? { token } : {})
      case 'PUT':
        return client.put<T>(endpoint, data, token ? { token } : {})
      case 'DELETE':
        return client.delete<T>(endpoint, token ? { token } : {})
      default:
        throw new Error(`Unsupported method: ${method}`)
    }
  }

  return {
    get: <T>(endpoint: string, token?: string | null) => request<T>('GET', endpoint, undefined, token),
    post: <T>(endpoint: string, data?: any, token?: string | null) => request<T>('POST', endpoint, data, token),
    put: <T>(endpoint: string, data?: any, token?: string | null) => request<T>('PUT', endpoint, data, token),
    delete: <T>(endpoint: string, token?: string | null) => request<T>('DELETE', endpoint, undefined, token),
  }
}

// Default client instance
export const apiClient = new ApiClient()