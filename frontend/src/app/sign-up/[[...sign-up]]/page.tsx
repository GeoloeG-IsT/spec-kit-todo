'use client'

import { SignUp } from '@clerk/nextjs'
import { Terminal, ArrowLeft, Zap, Shield, Globe, Database } from 'lucide-react'
import { Button, Card } from '../../../components/ui'
import Link from 'next/link'

export default function SignUpPage() {
  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="w-full max-w-4xl grid grid-cols-1 lg:grid-cols-2 gap-8 items-center">
        {/* Left side - Features */}
        <div className="space-y-6 order-2 lg:order-1">
          <div className="space-y-4">
            <Link
              href="/"
              className="inline-flex items-center gap-2 text-cyan-400 hover:text-cyan-300 font-mono text-sm transition-colors"
            >
              <ArrowLeft className="h-4 w-4" />
              Back to Terminal
            </Link>

            <div>
              <h2 className="text-2xl font-bold font-mono neon-text mb-2">
                Join the Network
              </h2>
              <p className="text-cyan-400/80 font-mono">
                Create your account and access advanced task management features
              </p>
            </div>
          </div>

          {/* Features Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Card className="p-4" glow="subtle">
              <div className="flex items-center gap-3 mb-2">
                <Zap className="h-6 w-6 text-cyan-400" />
                <h3 className="font-mono font-semibold text-cyan-300">Real-time Sync</h3>
              </div>
              <p className="text-sm text-cyan-400/70 font-mono">
                Your TODOs instantly sync across all connected devices and sessions
              </p>
            </Card>

            <Card className="p-4" glow="subtle">
              <div className="flex items-center gap-3 mb-2">
                <Shield className="h-6 w-6 text-purple-400" />
                <h3 className="font-mono font-semibold text-purple-300">Secure & Private</h3>
              </div>
              <p className="text-sm text-purple-400/70 font-mono">
                Military-grade encryption protects your data and privacy
              </p>
            </Card>

            <Card className="p-4" glow="subtle">
              <div className="flex items-center gap-3 mb-2">
                <Globe className="h-6 w-6 text-green-400" />
                <h3 className="font-mono font-semibold text-green-300">Multi-Platform</h3>
              </div>
              <p className="text-sm text-green-400/70 font-mono">
                Access from any device, anywhere in the cybernet
              </p>
            </Card>

            <Card className="p-4" glow="subtle">
              <div className="flex items-center gap-3 mb-2">
                <Database className="h-6 w-6 text-yellow-400" />
                <h3 className="font-mono font-semibold text-yellow-300">Cloud Backup</h3>
              </div>
              <p className="text-sm text-yellow-400/70 font-mono">
                Never lose your data with automatic cloud synchronization
              </p>
            </Card>
          </div>

          {/* Stats */}
          <Card className="p-4 border-cyan-500/30 bg-cyan-900/10">
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <div className="text-2xl font-bold font-mono text-cyan-300">10K+</div>
                <div className="text-xs text-cyan-400/70 font-mono">Active Users</div>
              </div>
              <div>
                <div className="text-2xl font-bold font-mono text-purple-300">99.9%</div>
                <div className="text-xs text-purple-400/70 font-mono">Uptime</div>
              </div>
              <div>
                <div className="text-2xl font-bold font-mono text-green-300">24/7</div>
                <div className="text-xs text-green-400/70 font-mono">Support</div>
              </div>
            </div>
          </Card>

          {/* Authentication Options Preview */}
          <Card className="p-4">
            <h3 className="font-mono font-semibold text-cyan-300 mb-3">
              Multiple Authentication Methods
            </h3>
            <div className="space-y-2">
              <div className="flex items-center gap-3 text-sm font-mono text-cyan-400/80">
                <div className="w-8 h-8 bg-white rounded flex items-center justify-center">
                  <span className="text-black font-bold text-xs">G</span>
                </div>
                <span>Continue with Google</span>
              </div>
              <div className="flex items-center gap-3 text-sm font-mono text-cyan-400/80">
                <div className="w-8 h-8 bg-gray-800 border border-cyan-500 rounded flex items-center justify-center">
                  <span className="text-cyan-400 font-bold text-xs">GH</span>
                </div>
                <span>Continue with GitHub</span>
              </div>
              <div className="flex items-center gap-3 text-sm font-mono text-cyan-400/80">
                <div className="w-8 h-8 bg-blue-600 rounded flex items-center justify-center">
                  <span className="text-white font-bold text-xs">in</span>
                </div>
                <span>Continue with LinkedIn</span>
              </div>
              <div className="flex items-center gap-3 text-sm font-mono text-cyan-400/80">
                <div className="w-8 h-8 bg-cyan-500 rounded flex items-center justify-center">
                  <span className="text-black font-bold text-xs">@</span>
                </div>
                <span>Email & Password</span>
              </div>
            </div>
          </Card>
        </div>

        {/* Right side - Sign-up Form */}
        <div className="space-y-6 order-1 lg:order-2">
          <div className="text-center space-y-4">
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
          </div>

          {/* Sign-up Component */}
          <div className="relative">
            <Card className="p-1 border-cyan-500" glow="normal">
              <div className="relative z-10">
                <SignUp
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

          {/* Terms and Privacy */}
          <Card className="p-4 border-cyan-500/30 bg-cyan-900/10">
            <p className="text-xs text-cyan-400/70 font-mono text-center">
              By creating an account, you agree to our{' '}
              <span className="text-cyan-400 hover:text-cyan-300 cursor-pointer underline">
                Terms of Service
              </span>{' '}
              and{' '}
              <span className="text-cyan-400 hover:text-cyan-300 cursor-pointer underline">
                Privacy Policy
              </span>
            </p>
          </Card>

          {/* Footer */}
          <div className="text-center">
            <p className="text-xs text-cyan-400/60 font-mono">
              Powered by Clerk Authentication Protocol
            </p>
            <p className="text-xs text-cyan-400/40 font-mono mt-1">
              Your data is encrypted and secured
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}