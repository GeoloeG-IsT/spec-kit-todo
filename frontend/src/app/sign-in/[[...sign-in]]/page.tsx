'use client'

import { SignIn } from '@clerk/nextjs'
import { Terminal, ArrowLeft } from 'lucide-react'
import { Button, Card } from '../../../components/ui'
import Link from 'next/link'

export default function SignInPage() {
  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="w-full max-w-md space-y-6">
        {/* Header */}
        <div className="text-center space-y-4">
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-cyan-400 hover:text-cyan-300 font-mono text-sm transition-colors mb-4"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Terminal
          </Link>

          <div className="flex items-center justify-center gap-3">
            <div className="relative">
              <Terminal className="h-10 w-10 text-cyan-400" />
              <div className="absolute -top-1 -right-1 w-4 h-4 bg-cyan-400 rounded-full animate-pulse" />
            </div>
            <div className="text-left">
              <h1 className="text-2xl font-bold font-mono neon-text">
                TODO.exe
              </h1>
              <p className="text-sm text-cyan-400/70 font-mono">
                Cyberpunk Task Manager
              </p>
            </div>
          </div>

          <div className="space-y-2">
            <h2 className="text-xl font-bold font-mono text-cyan-300">
              Access Terminal
            </h2>
            <p className="text-cyan-400/80 font-mono text-sm">
              Authenticate to sync your tasks across the network
            </p>
          </div>
        </div>

        {/* Sign-in Component */}
        <div className="relative">
          <Card className="p-1 border-cyan-500" glow="normal">
            <div className="relative z-10">
              <SignIn
                appearance={{
                  elements: {
                    rootBox: 'w-full',
                    card: 'bg-gray-900 border-none shadow-none',
                    headerTitle: 'text-cyan-300 font-mono text-lg',
                    headerSubtitle: 'text-cyan-400/80 font-mono text-sm',
                    socialButtonsBlockButton: 'bg-gray-800 border border-cyan-500 text-cyan-100 hover:bg-cyan-500/10 hover:border-cyan-400 font-mono',
                    socialButtonsBlockButtonText: 'text-cyan-100 font-mono',
                    dividerLine: 'bg-cyan-500/30',
                    dividerText: 'text-cyan-400 font-mono text-sm',
                    formFieldLabel: 'text-cyan-300 font-mono',
                    formFieldInput: 'bg-gray-800 border-cyan-500 text-cyan-100 font-mono placeholder:text-cyan-400/60 focus:border-cyan-300 focus:ring-cyan-500',
                    formButtonPrimary: 'bg-cyan-500 text-black hover:bg-cyan-400 font-mono font-bold border border-cyan-300 shadow-neon-sm hover:shadow-neon',
                    footerActionLink: 'text-cyan-400 hover:text-cyan-300 font-mono',
                    identityPreviewEditButton: 'text-cyan-400 hover:text-cyan-300 font-mono',
                    formFieldErrorText: 'text-red-400 font-mono text-sm',
                    formFieldSuccessText: 'text-green-400 font-mono text-sm',
                    formFieldWarningText: 'text-yellow-400 font-mono text-sm',
                    formFieldHintText: 'text-cyan-400/70 font-mono text-sm',
                    otpCodeFieldInput: 'bg-gray-800 border-cyan-500 text-cyan-100 font-mono focus:border-cyan-300 focus:ring-cyan-500',
                    formResendCodeLink: 'text-cyan-400 hover:text-cyan-300 font-mono',
                    alertClerkError: 'border-red-500 bg-red-900/20 text-red-400',
                  },
                }}
                redirectUrl="/"
                fallbackRedirectUrl="/"
              />
            </div>
          </Card>

          {/* Decorative elements */}
          <div className="absolute -inset-4 bg-gradient-to-r from-cyan-500/10 via-purple-500/10 to-cyan-500/10 rounded-lg opacity-50 blur-xl" />
        </div>

        {/* Info Section */}
        <Card className="p-4 border-cyan-500/30 bg-cyan-900/10">
          <div className="space-y-3">
            <h3 className="font-mono font-semibold text-cyan-300 text-center">
              Security Features
            </h3>
            <div className="grid grid-cols-1 gap-2 text-sm font-mono">
              <div className="flex items-center gap-2 text-cyan-400/80">
                <div className="w-2 h-2 bg-cyan-400 rounded-full" />
                <span>End-to-end encryption</span>
              </div>
              <div className="flex items-center gap-2 text-cyan-400/80">
                <div className="w-2 h-2 bg-green-400 rounded-full" />
                <span>Multi-factor authentication</span>
              </div>
              <div className="flex items-center gap-2 text-cyan-400/80">
                <div className="w-2 h-2 bg-purple-400 rounded-full" />
                <span>Real-time synchronization</span>
              </div>
            </div>
          </div>
        </Card>

        {/* Footer */}
        <div className="text-center">
          <p className="text-xs text-cyan-400/60 font-mono">
            Powered by Clerk Authentication Protocol
          </p>
          <p className="text-xs text-cyan-400/40 font-mono mt-1">
            All connections are secured with 256-bit encryption
          </p>
        </div>
      </div>
    </div>
  )
}