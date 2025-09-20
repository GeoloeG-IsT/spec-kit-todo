'use client'

import { useUser, UserProfile as ClerkUserProfile } from '@clerk/nextjs'
import { ArrowLeft, User, Settings, Shield, Activity, Database, Clock } from 'lucide-react'
import { Card, Button } from '../../../components/ui'
import { UserProfile } from '../../../components/features'
import Link from 'next/link'
import { useTodos } from '../../../lib/hooks/useTodos'
import { useMemo } from 'react'

export default function ProfilePage() {
  const { user, isLoaded } = useUser()
  const { todos } = useTodos()

  const stats = useMemo(() => {
    if (!todos) return null

    const totalTodos = todos.length
    const completedTodos = todos.filter(todo => todo.completed).length
    const activeTodos = totalTodos - completedTodos
    const completionRate = totalTodos > 0 ? (completedTodos / totalTodos) * 100 : 0

    const priorityStats = {
      high: todos.filter(todo => todo.priority === 'high').length,
      medium: todos.filter(todo => todo.priority === 'medium').length,
      low: todos.filter(todo => todo.priority === 'low').length,
    }

    const recentActivity = todos
      .sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())
      .slice(0, 5)

    return {
      totalTodos,
      completedTodos,
      activeTodos,
      completionRate,
      priorityStats,
      recentActivity,
    }
  }, [todos])

  if (!isLoaded) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-cyan-500 border-t-transparent" />
      </div>
    )
  }

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Card className="p-8 text-center">
          <h1 className="text-xl font-mono text-red-400 mb-4">Access Denied</h1>
          <p className="text-cyan-400/80 font-mono mb-4">
            You must be authenticated to access this terminal
          </p>
          <Link href="/sign-in">
            <Button>Authenticate</Button>
          </Link>
        </Card>
      </div>
    )
  }

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="border-b border-cyan-500/20 bg-gray-900/80 backdrop-blur-sm">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center gap-4">
            <Link
              href="/"
              className="inline-flex items-center gap-2 text-cyan-400 hover:text-cyan-300 font-mono text-sm transition-colors"
            >
              <ArrowLeft className="h-4 w-4" />
              Back to Terminal
            </Link>
            <div className="flex items-center gap-2">
              <User className="h-5 w-5 text-cyan-400" />
              <h1 className="text-xl font-bold font-mono neon-text">
                User Profile Terminal
              </h1>
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Sidebar - User Info & Stats */}
          <div className="space-y-6">
            {/* User Profile Card */}
            <UserProfile showDetails={true} />

            {/* Task Statistics */}
            {stats && (
              <Card className="p-4" glow="subtle">
                <div className="flex items-center gap-2 mb-4">
                  <Activity className="h-5 w-5 text-cyan-400" />
                  <h2 className="font-mono font-semibold text-cyan-300">Task Statistics</h2>
                </div>

                <div className="space-y-4">
                  {/* Overall Stats */}
                  <div className="grid grid-cols-2 gap-4">
                    <div className="text-center p-3 bg-gray-800/50 rounded border border-cyan-500/20">
                      <div className="text-xl font-bold font-mono text-cyan-300">
                        {stats.totalTodos}
                      </div>
                      <div className="text-xs text-cyan-400/70 font-mono">Total Tasks</div>
                    </div>
                    <div className="text-center p-3 bg-gray-800/50 rounded border border-green-500/20">
                      <div className="text-xl font-bold font-mono text-green-300">
                        {stats.completedTodos}
                      </div>
                      <div className="text-xs text-green-400/70 font-mono">Completed</div>
                    </div>
                  </div>

                  {/* Completion Rate */}
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm text-cyan-400 font-mono">Completion Rate</span>
                      <span className="text-sm text-cyan-300 font-mono font-bold">
                        {stats.completionRate.toFixed(1)}%
                      </span>
                    </div>
                    <div className="w-full bg-gray-800 rounded-full h-2">
                      <div
                        className="bg-gradient-to-r from-cyan-500 to-green-500 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${stats.completionRate}%` }}
                      />
                    </div>
                  </div>

                  {/* Priority Breakdown */}
                  <div>
                    <h3 className="text-sm text-cyan-400 font-mono mb-2">Priority Breakdown</h3>
                    <div className="space-y-2">
                      <div className="flex justify-between items-center">
                        <span className="text-xs text-red-400 font-mono">High Priority</span>
                        <span className="text-xs text-red-300 font-mono font-bold">
                          {stats.priorityStats.high}
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-xs text-yellow-400 font-mono">Medium Priority</span>
                        <span className="text-xs text-yellow-300 font-mono font-bold">
                          {stats.priorityStats.medium}
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-xs text-green-400 font-mono">Low Priority</span>
                        <span className="text-xs text-green-300 font-mono font-bold">
                          {stats.priorityStats.low}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </Card>
            )}

            {/* Recent Activity */}
            {stats?.recentActivity && stats.recentActivity.length > 0 && (
              <Card className="p-4" glow="subtle">
                <div className="flex items-center gap-2 mb-4">
                  <Clock className="h-5 w-5 text-purple-400" />
                  <h2 className="font-mono font-semibold text-purple-300">Recent Activity</h2>
                </div>

                <div className="space-y-2">
                  {stats.recentActivity.map((todo) => (
                    <div
                      key={todo.id}
                      className="flex items-center gap-3 p-2 bg-gray-800/30 rounded border border-purple-500/10"
                    >
                      <div
                        className={`w-2 h-2 rounded-full ${
                          todo.completed ? 'bg-green-400' : 'bg-cyan-400'
                        }`}
                      />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-cyan-100 font-mono truncate">
                          {todo.title}
                        </p>
                        <p className="text-xs text-cyan-400/60 font-mono">
                          {new Date(todo.updated_at).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            )}
          </div>

          {/* Main Content - User Profile Settings */}
          <div className="lg:col-span-2">
            <Card className="p-1 border-cyan-500" glow="normal">
              <div className="relative z-10">
                <ClerkUserProfile
                  appearance={{
                    elements: {
                      rootBox: 'w-full',
                      card: 'bg-gray-900 border-none shadow-none',
                      headerTitle: 'text-cyan-300 font-mono text-lg',
                      headerSubtitle: 'text-cyan-400/80 font-mono text-sm',
                      navbar: 'bg-gray-800 border-b border-cyan-500/20',
                      navbarButton: 'text-cyan-400 hover:text-cyan-300 font-mono hover:bg-cyan-500/10',
                      navbarButtonActive: 'text-cyan-300 bg-cyan-500/20 border-r-2 border-cyan-400',
                      pageScrollBox: 'bg-gray-900',
                      formFieldLabel: 'text-cyan-300 font-mono',
                      formFieldInput: 'bg-gray-800 border-cyan-500 text-cyan-100 font-mono placeholder:text-cyan-400/60 focus:border-cyan-300 focus:ring-cyan-500',
                      formButtonPrimary: 'bg-cyan-500 text-black hover:bg-cyan-400 font-mono font-bold border border-cyan-300 shadow-neon-sm hover:shadow-neon',
                      formButtonSecondary: 'bg-gray-800 text-cyan-400 border-cyan-500 hover:bg-cyan-500/10 hover:border-cyan-400 font-mono',
                      badge: 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/50 font-mono',
                      formFieldErrorText: 'text-red-400 font-mono text-sm',
                      formFieldSuccessText: 'text-green-400 font-mono text-sm',
                      formFieldWarningText: 'text-yellow-400 font-mono text-sm',
                      formFieldHintText: 'text-cyan-400/70 font-mono text-sm',
                      identityPreviewText: 'text-cyan-100 font-mono',
                      identityPreviewEditButton: 'text-cyan-400 hover:text-cyan-300 font-mono',
                      profileSectionTitle: 'text-cyan-300 font-mono text-base',
                      profileSectionContent: 'text-cyan-100 font-mono',
                      alertClerkError: 'border-red-500 bg-red-900/20 text-red-400',
                      alertClerkInfo: 'border-cyan-500 bg-cyan-900/20 text-cyan-400',
                      alertClerkSuccess: 'border-green-500 bg-green-900/20 text-green-400',
                      tableHead: 'text-cyan-300 font-mono bg-gray-800',
                      tableCell: 'text-cyan-100 font-mono border-cyan-500/20',
                      modalContent: 'bg-gray-900 border border-cyan-500',
                      modalCloseButton: 'text-cyan-400 hover:text-cyan-300',
                    },
                  }}
                />
              </div>

              {/* Decorative background */}
              <div className="absolute -inset-4 bg-gradient-to-r from-cyan-500/5 via-purple-500/5 to-cyan-500/5 rounded-lg opacity-50 blur-xl pointer-events-none" />
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}