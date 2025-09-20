'use client'

import { useState, useEffect } from 'react'
import { Terminal, Cpu, Database, Wifi, WifiOff } from 'lucide-react'
import { Card, Button } from '../components/ui'
import {
  TodoList,
  AddTodoForm,
  UserProfile,
  AuthButtons,
} from '../components/features'
import { useTodos } from '../lib/hooks/useTodos'
import { useSession } from '../lib/hooks/useSession'
import { useRealTimeSync } from '../lib/hooks/useRealTimeSync'
import { useAuth } from '../lib/hooks/useAuth'
import { TodoItemCreate, TodoItemResponse } from '../lib/api/types'

export default function HomePage() {
  const { isAuthenticated, isLoading } = useAuth()
  const [isOnline, setIsOnline] = useState(true)

  // Check online status
  useEffect(() => {
    const handleOnline = () => setIsOnline(true)
    const handleOffline = () => setIsOnline(false)

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)
    setIsOnline(navigator.onLine)

    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="border-b border-cyan-500/20 bg-gray-900/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            {/* Logo and Title */}
            <div className="flex items-center gap-3">
              <div className="relative">
                <Terminal className="h-8 w-8 text-cyan-400" />
                <div className="absolute -top-1 -right-1 w-3 h-3 bg-cyan-400 rounded-full animate-pulse" />
              </div>
              <div>
                <h1 className="text-xl font-bold font-mono neon-text">
                  TODO.exe
                </h1>
                <p className="text-xs text-cyan-400/70 font-mono">
                  Cyberpunk Task Manager v2.0.1
                </p>
              </div>
            </div>

            {/* Status Indicators */}
            <div className="flex items-center gap-4">
              {/* Connection Status */}
              <div className="flex items-center gap-2 text-sm font-mono">
                {isOnline ? (
                  <>
                    <Wifi className="h-4 w-4 text-green-400" />
                    <span className="text-green-400">ONLINE</span>
                  </>
                ) : (
                  <>
                    <WifiOff className="h-4 w-4 text-red-400" />
                    <span className="text-red-400">OFFLINE</span>
                  </>
                )}
              </div>

              {/* Auth Section */}
              {isAuthenticated && (
                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-2 text-sm font-mono text-cyan-400">
                    <Database className="h-4 w-4" />
                    <span>SYNC</span>
                  </div>
                </div>
              )}

              {!isAuthenticated && !isLoading && (
                <AuthButtons variant="compact" />
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Sidebar */}
          <aside className="lg:col-span-1 space-y-6">
            {/* System Info */}
            <Card className="p-4" glow="subtle">
              <div className="flex items-center gap-2 mb-3">
                <Cpu className="h-5 w-5 text-cyan-400" />
                <h2 className="font-mono font-semibold text-cyan-300">System Status</h2>
              </div>
              <div className="space-y-2 text-sm font-mono">
                <div className="flex justify-between">
                  <span className="text-cyan-400">CPU:</span>
                  <span className="text-green-400">98.7%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-cyan-400">Memory:</span>
                  <span className="text-yellow-400">67.3%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-cyan-400">Network:</span>
                  <span className={isOnline ? 'text-green-400' : 'text-red-400'}>
                    {isOnline ? 'STABLE' : 'DISCONNECTED'}
                  </span>
                </div>
              </div>
            </Card>

            {/* User Profile */}
            {isAuthenticated && (
              <UserProfile />
            )}

            {/* Auth for signed-out users */}
            {!isAuthenticated && !isLoading && (
              <AuthButtons showBenefits={false} />
            )}
          </aside>

          {/* Main TODO Area */}
          <section className="lg:col-span-3">
            {isAuthenticated && (
              <AuthenticatedTodoApp />
            )}

            {!isAuthenticated && !isLoading && (
              <GuestTodoApp />
            )}

            {isLoading && (
              <div className="flex items-center justify-center py-12">
                <div className="text-cyan-400 font-mono">Loading...</div>
              </div>
            )}
          </section>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-cyan-500/20 bg-gray-900/80 backdrop-blur-sm mt-16">
        <div className="container mx-auto px-4 py-6">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <p className="text-sm text-cyan-400/70 font-mono">
              © 2025 TODO.exe - Cyberpunk Task Management System
            </p>
            <div className="flex items-center gap-4 text-sm text-cyan-400/70 font-mono">
              <span>v2.0.1</span>
              <span>•</span>
              <span>Built with Next.js & FastAPI</span>
              <span>•</span>
              <span className="flex items-center gap-1">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                All systems operational
              </span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}

// Authenticated user TODO app
function AuthenticatedTodoApp() {
  const {
    todos,
    loading,
    createTodo,
    updateTodo,
    deleteTodo,
    reorderTodos,
  } = useTodos()

  // Enable real-time sync for authenticated users
  useRealTimeSync()

  const handleAddTodo = async (todoData: TodoItemCreate) => {
    try {
      await createTodo.mutateAsync(todoData)
    } catch (error) {
      console.error('Failed to create TODO:', error)
    }
  }

  const handleUpdateTodo = async (updates: Partial<TodoItemResponse> & { id: string }) => {
    try {
      await updateTodo.mutateAsync(updates)
    } catch (error) {
      console.error('Failed to update TODO:', error)
    }
  }

  const handleDeleteTodo = async (id: string) => {
    try {
      await deleteTodo.mutateAsync(id)
    } catch (error) {
      console.error('Failed to delete TODO:', error)
    }
  }

  const handleReorderTodos = async (reorderData: Array<{ todo_id: string; order_index: number }>) => {
    try {
      await reorderTodos.mutateAsync({ todo_orders: reorderData })
    } catch (error) {
      console.error('Failed to reorder TODOs:', error)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold font-mono neon-text">
          Task Management Terminal
        </h1>
        <div className="flex items-center gap-2 text-sm font-mono text-cyan-400">
          <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
          <span>Synced</span>
        </div>
      </div>

      <AddTodoForm
        onAddTodo={handleAddTodo}
        loading={createTodo.isPending}
      />

      <TodoList
        todos={todos}
        loading={loading}
        onUpdateTodo={handleUpdateTodo}
        onDeleteTodo={handleDeleteTodo}
        onReorderTodos={handleReorderTodos}
      />
    </div>
  )
}

// Guest user TODO app
function GuestTodoApp() {
  const { sessionId } = useSession()
  const {
    todos,
    loading,
    createTodo,
    updateTodo,
    deleteTodo,
    reorderTodos,
  } = useTodos()

  const handleAddTodo = async (todoData: TodoItemCreate) => {
    try {
      await createTodo.mutateAsync(todoData)
    } catch (error) {
      console.error('Failed to create TODO:', error)
    }
  }

  const handleUpdateTodo = async (updates: Partial<TodoItemResponse> & { id: string }) => {
    try {
      await updateTodo.mutateAsync(updates)
    } catch (error) {
      console.error('Failed to update TODO:', error)
    }
  }

  const handleDeleteTodo = async (id: string) => {
    try {
      await deleteTodo.mutateAsync(id)
    } catch (error) {
      console.error('Failed to delete TODO:', error)
    }
  }

  const handleReorderTodos = async (reorderData: Array<{ todo_id: string; order_index: number }>) => {
    try {
      await reorderTodos.mutateAsync({ todo_orders: reorderData })
    } catch (error) {
      console.error('Failed to reorder TODOs:', error)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold font-mono neon-text mb-2">
          Guest Terminal Access
        </h1>
        <p className="text-cyan-400/80 font-mono text-sm">
          Your TODOs are stored locally. Sign in to sync across devices.
        </p>
        {sessionId && (
          <p className="text-cyan-400/60 font-mono text-xs mt-1">
            Session ID: {sessionId.slice(0, 8)}...
          </p>
        )}
      </div>

      <Card className="p-4 border-yellow-500/50 bg-yellow-900/10">
        <div className="flex items-start gap-3">
          <div className="w-6 h-6 bg-yellow-500 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
            <span className="text-black text-xs font-bold">!</span>
          </div>
          <div>
            <h3 className="font-mono font-semibold text-yellow-300 mb-1">
              Guest Mode Active
            </h3>
            <p className="text-yellow-400/80 font-mono text-sm">
              Your TODOs will be lost when you close the browser.
              Sign in to save your progress and sync across devices.
            </p>
          </div>
        </div>
      </Card>

      <AddTodoForm
        onAddTodo={handleAddTodo}
        loading={createTodo.isPending}
      />

      <TodoList
        todos={todos}
        loading={loading}
        onUpdateTodo={handleUpdateTodo}
        onDeleteTodo={handleDeleteTodo}
        onReorderTodos={handleReorderTodos}
      />
    </div>
  )
}