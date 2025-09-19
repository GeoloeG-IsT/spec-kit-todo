/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Cyberpunk theme colors
        'neon-cyan': '#00FFFF',
        'neon-magenta': '#FF00FF',
        'electric-purple': '#8A2BE2',
        'cyber-dark': '#0a0a0f',
        'cyber-gray': '#1a1a2e',
        'cyber-blue': '#16213e',
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      animation: {
        'scanline': 'scanline 2s linear infinite',
        'glitch': 'glitch 0.3s ease-in-out',
        'pulse-neon': 'pulse-neon 2s ease-in-out infinite',
      },
      keyframes: {
        scanline: {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100vh)' },
        },
        glitch: {
          '0%': { transform: 'translate(0)' },
          '20%': { transform: 'translate(-2px, 2px)' },
          '40%': { transform: 'translate(-2px, -2px)' },
          '60%': { transform: 'translate(2px, 2px)' },
          '80%': { transform: 'translate(2px, -2px)' },
          '100%': { transform: 'translate(0)' },
        },
        'pulse-neon': {
          '0%, 100%': {
            boxShadow: '0 0 5px currentColor, 0 0 10px currentColor, 0 0 20px currentColor'
          },
          '50%': {
            boxShadow: '0 0 2px currentColor, 0 0 5px currentColor, 0 0 10px currentColor'
          },
        },
      },
      boxShadow: {
        'neon': '0 0 5px currentColor, 0 0 10px currentColor, 0 0 20px currentColor',
        'neon-sm': '0 0 2px currentColor, 0 0 5px currentColor',
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
  ],
}