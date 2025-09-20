import type { Metadata } from 'next'
import { Inter, JetBrains_Mono } from 'next/font/google'
import './globals.css'
import { Providers } from './providers'

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
})

const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  variable: '--font-jetbrains-mono',
})

export const metadata: Metadata = {
  title: 'TODO List - Cyberpunk Edition',
  description: 'A futuristic TODO list application with real-time sync and cyberpunk aesthetics',
  keywords: ['todo', 'cyberpunk', 'productivity', 'real-time', 'sync'],
  authors: [{ name: 'TODO List App' }],
  viewport: 'width=device-width, initial-scale=1',
  robots: 'index, follow',
  openGraph: {
    title: 'TODO List - Cyberpunk Edition',
    description: 'A futuristic TODO list application with real-time sync',
    type: 'website',
    locale: 'en_US',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <body
        className={`${inter.variable} ${jetbrainsMono.variable} font-sans antialiased bg-gray-900 text-cyan-100 min-h-screen`}
      >
        <div className="cyberpunk-bg">
          <div className="scanlines" />
          <Providers>
            <main className="min-h-screen relative z-10">
              {children}
            </main>
          </Providers>
        </div>
      </body>
    </html>
  )
}