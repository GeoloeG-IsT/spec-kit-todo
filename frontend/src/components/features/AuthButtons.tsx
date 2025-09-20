import { SignInButton, SignUpButton, SignedIn, SignedOut, useUser } from '@clerk/nextjs'
import { LogIn, UserPlus, Zap, Shield, Globe } from 'lucide-react'
import { Button, Card } from '../ui'
import { clsx } from 'clsx'

interface AuthButtonsProps {
  className?: string
  variant?: 'default' | 'compact' | 'hero'
  showBenefits?: boolean
}

export function AuthButtons({
  className,
  variant = 'default',
  showBenefits = false
}: AuthButtonsProps) {
  const { user } = useUser()

  if (variant === 'hero') {
    return (
      <div className={clsx('text-center space-y-6', className)}>
        <SignedOut>
          <div className="space-y-4">
            <h2 className="text-2xl font-bold font-mono neon-text">
              Ready to boost your productivity?
            </h2>
            <p className="text-cyan-400/80 font-mono">
              Join thousands of users managing their tasks with style
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <SignUpButton mode="modal">
                <Button size="lg" className="group">
                  <UserPlus className="h-5 w-5 group-hover:scale-110 transition-transform" />
                  Get Started Free
                </Button>
              </SignUpButton>

              <SignInButton mode="modal">
                <Button variant="secondary" size="lg" className="group">
                  <LogIn className="h-5 w-5 group-hover:scale-110 transition-transform" />
                  Sign In
                </Button>
              </SignInButton>
            </div>

            {showBenefits && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8">
                <Card className="p-4 text-center" glow="subtle">
                  <Zap className="h-8 w-8 text-cyan-400 mx-auto mb-2" />
                  <h3 className="font-mono font-semibold text-cyan-300 mb-1">Real-time Sync</h3>
                  <p className="text-sm text-cyan-400/70 font-mono">
                    Your TODOs sync instantly across all devices
                  </p>
                </Card>

                <Card className="p-4 text-center" glow="subtle">
                  <Shield className="h-8 w-8 text-purple-400 mx-auto mb-2" />
                  <h3 className="font-mono font-semibold text-purple-300 mb-1">Secure & Private</h3>
                  <p className="text-sm text-purple-400/70 font-mono">
                    Your data is encrypted and protected
                  </p>
                </Card>

                <Card className="p-4 text-center" glow="subtle">
                  <Globe className="h-8 w-8 text-green-400 mx-auto mb-2" />
                  <h3 className="font-mono font-semibold text-green-300 mb-1">Multiple Auth</h3>
                  <p className="text-sm text-green-400/70 font-mono">
                    Sign in with Google, GitHub, or LinkedIn
                  </p>
                </Card>
              </div>
            )}
          </div>
        </SignedOut>

        <SignedIn>
          <div className="space-y-4">
            <h2 className="text-2xl font-bold font-mono neon-text">
              Welcome back, {user?.firstName || 'User'}!
            </h2>
            <p className="text-cyan-400/80 font-mono">
              Ready to tackle your TODOs?
            </p>
          </div>
        </SignedIn>
      </div>
    )
  }

  if (variant === 'compact') {
    return (
      <div className={clsx('flex items-center gap-2', className)}>
        <SignedOut>
          <SignInButton mode="modal">
            <Button variant="ghost" size="sm">
              <LogIn className="h-4 w-4" />
              Sign In
            </Button>
          </SignInButton>

          <SignUpButton mode="modal">
            <Button size="sm">
              <UserPlus className="h-4 w-4" />
              Sign Up
            </Button>
          </SignUpButton>
        </SignedOut>
      </div>
    )
  }

  // Default variant
  return (
    <Card className={clsx('p-6', className)} glow="subtle">
      <SignedOut>
        <div className="text-center space-y-4">
          <div className="space-y-2">
            <h3 className="text-lg font-bold font-mono neon-text">
              Sign in to sync your TODOs
            </h3>
            <p className="text-cyan-400/80 font-mono text-sm">
              Access your tasks from anywhere, anytime
            </p>
          </div>

          <div className="space-y-3">
            <SignUpButton mode="modal">
              <Button className="w-full group">
                <UserPlus className="h-4 w-4 group-hover:scale-110 transition-transform" />
                Create Account
              </Button>
            </SignUpButton>

            <SignInButton mode="modal">
              <Button variant="secondary" className="w-full group">
                <LogIn className="h-4 w-4 group-hover:scale-110 transition-transform" />
                Sign In
              </Button>
            </SignInButton>
          </div>

          <div className="pt-4 border-t border-cyan-500/20">
            <p className="text-xs text-cyan-400/60 font-mono">
              Continue as guest to try it out, or sign in to save your progress
            </p>
          </div>
        </div>
      </SignedOut>

      <SignedIn>
        <div className="text-center space-y-2">
          <div className="w-12 h-12 bg-gradient-to-r from-cyan-500 to-purple-500 rounded-full mx-auto flex items-center justify-center">
            <Shield className="h-6 w-6 text-white" />
          </div>
          <h3 className="text-lg font-bold font-mono neon-text">
            You're signed in!
          </h3>
          <p className="text-cyan-400/80 font-mono text-sm">
            Your TODOs are synced and secure
          </p>
        </div>
      </SignedIn>
    </Card>
  )
}

// Individual button components for more specific use cases
export function SignInButtonComponent({
  className,
  variant = 'primary',
  size = 'md',
  children
}: {
  className?: string
  variant?: 'primary' | 'secondary' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
  children?: React.ReactNode
}) {
  return (
    <SignInButton mode="modal">
      <Button variant={variant} size={size} className={className}>
        <LogIn className="h-4 w-4" />
        {children || 'Sign In'}
      </Button>
    </SignInButton>
  )
}

export function SignUpButtonComponent({
  className,
  variant = 'primary',
  size = 'md',
  children
}: {
  className?: string
  variant?: 'primary' | 'secondary' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
  children?: React.ReactNode
}) {
  return (
    <SignUpButton mode="modal">
      <Button variant={variant} size={size} className={className}>
        <UserPlus className="h-4 w-4" />
        {children || 'Sign Up'}
      </Button>
    </SignUpButton>
  )
}