import { UserButton, useUser } from '@clerk/nextjs'
import { User, Calendar, Shield, Settings } from 'lucide-react'
import { Card, Button } from '../ui'
import { clsx } from 'clsx'

interface UserProfileProps {
  className?: string
  showDetails?: boolean
}

export function UserProfile({ className, showDetails = true }: UserProfileProps) {
  const { user, isLoaded } = useUser()

  if (!isLoaded) {
    return (
      <Card className={clsx('p-4', className)}>
        <div className="animate-pulse flex items-center space-x-3">
          <div className="rounded-full bg-cyan-500/20 h-10 w-10" />
          <div className="space-y-2">
            <div className="h-4 bg-cyan-500/20 rounded w-24" />
            <div className="h-3 bg-cyan-500/20 rounded w-32" />
          </div>
        </div>
      </Card>
    )
  }

  if (!user) {
    return null
  }

  const formatDate = (date: Date) => {
    return new Intl.DateTimeFormat('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    }).format(date)
  }

  const getAccountType = () => {
    if (user.externalAccounts.length > 0) {
      const providers = user.externalAccounts.map(account => account.provider)
      return providers.join(', ')
    }
    return 'Email'
  }

  return (
    <Card className={clsx('transition-all duration-300', className)} glow="subtle">
      <div className="flex items-start gap-4">
        {/* Avatar */}
        <div className="relative">
          <UserButton
            appearance={{
              elements: {
                avatarBox: 'w-12 h-12 border-2 border-cyan-500 shadow-neon-sm hover:shadow-neon transition-all duration-200',
                userButtonPopoverCard: 'bg-gray-900 border border-cyan-500 shadow-neon',
                userButtonPopoverMain: 'text-cyan-100',
                userButtonPopoverFooter: 'border-t border-cyan-500/20',
              },
            }}
          />
          <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-green-500 rounded-full border-2 border-gray-900 animate-pulse" />
        </div>

        {/* User Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-mono font-semibold text-cyan-300 neon-text">
                {user.fullName || user.username || 'Anonymous User'}
              </h3>
              <p className="text-sm text-cyan-400/80 font-mono">
                {user.primaryEmailAddress?.emailAddress}
              </p>
            </div>
          </div>

          {showDetails && (
            <div className="mt-4 space-y-3">
              {/* Account Stats */}
              <div className="grid grid-cols-2 gap-4 p-3 bg-gray-800/50 rounded border border-cyan-500/20">
                <div className="text-center">
                  <div className="text-cyan-300 font-mono font-bold text-lg">
                    {user.createdAt ? Math.floor((Date.now() - user.createdAt.getTime()) / (1000 * 60 * 60 * 24)) : 0}
                  </div>
                  <div className="text-xs text-cyan-400/70 font-mono">Days Active</div>
                </div>
                <div className="text-center">
                  <div className="text-purple-300 font-mono font-bold text-lg">
                    {user.externalAccounts.length + (user.passwordEnabled ? 1 : 0)}
                  </div>
                  <div className="text-xs text-purple-400/70 font-mono">Auth Methods</div>
                </div>
              </div>

              {/* Account Details */}
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-sm text-cyan-400/80 font-mono">
                  <Calendar className="h-4 w-4" />
                  <span>Joined {user.createdAt ? formatDate(user.createdAt) : 'Unknown'}</span>
                </div>

                <div className="flex items-center gap-2 text-sm text-cyan-400/80 font-mono">
                  <Shield className="h-4 w-4" />
                  <span>Account Type: {getAccountType()}</span>
                </div>

                {user.lastSignInAt && (
                  <div className="flex items-center gap-2 text-sm text-cyan-400/80 font-mono">
                    <User className="h-4 w-4" />
                    <span>Last active: {formatDate(user.lastSignInAt)}</span>
                  </div>
                )}
              </div>

              {/* Connected Accounts */}
              {user.externalAccounts.length > 0 && (
                <div>
                  <h4 className="text-sm font-mono font-medium text-cyan-300 mb-2 flex items-center gap-2">
                    <Settings className="h-4 w-4" />
                    Connected Accounts
                  </h4>
                  <div className="space-y-1">
                    {user.externalAccounts.map((account) => (
                      <div
                        key={account.id}
                        className="flex items-center gap-2 text-sm text-cyan-400/80 font-mono p-2 bg-gray-800/30 rounded border border-cyan-500/10"
                      >
                        <div className="w-4 h-4 rounded bg-cyan-500/20 flex items-center justify-center">
                          <span className="text-xs text-cyan-300">
                            {account.provider.charAt(0).toUpperCase()}
                          </span>
                        </div>
                        <span className="capitalize">{account.provider}</span>
                        {account.emailAddress && (
                          <span className="text-cyan-400/60">({account.emailAddress})</span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Quick Actions */}
              <div className="pt-3 border-t border-cyan-500/20">
                <div className="flex gap-2">
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => user.openManageAccountModal?.()}
                    className="flex-1"
                  >
                    <Settings className="h-3 w-3" />
                    Manage Account
                  </Button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </Card>
  )
}