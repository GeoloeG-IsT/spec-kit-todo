import { ButtonHTMLAttributes, forwardRef } from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { clsx } from 'clsx'

const buttonVariants = cva(
  'inline-flex items-center justify-center rounded-md text-sm font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 font-mono transform hover:scale-105 glitch-hover',
  {
    variants: {
      variant: {
        primary: 'bg-cyan-500 text-black hover:bg-cyan-400 border border-cyan-300 shadow-neon-sm hover:shadow-neon',
        secondary: 'bg-transparent text-purple-400 hover:text-purple-300 border border-purple-500 hover:border-purple-400 hover:bg-purple-500 hover:bg-opacity-20 hover:shadow-neon-sm',
        danger: 'bg-transparent text-red-400 hover:text-red-300 border border-red-500 hover:border-red-400 hover:bg-red-500 hover:bg-opacity-20 hover:shadow-neon-sm',
        ghost: 'text-cyan-400 hover:text-cyan-300 hover:bg-cyan-500 hover:bg-opacity-10',
        link: 'text-cyan-400 underline-offset-4 hover:underline hover:text-cyan-300 p-0',
      },
      size: {
        sm: 'h-8 px-3 text-xs',
        md: 'h-10 px-4 py-2',
        lg: 'h-12 px-8 text-base',
        icon: 'h-10 w-10',
      },
    },
    defaultVariants: {
      variant: 'primary',
      size: 'md',
    },
  }
)

export interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  loading?: boolean
  leftIcon?: React.ReactNode
  rightIcon?: React.ReactNode
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, loading, leftIcon, rightIcon, children, disabled, ...props }, ref) => {
    return (
      <button
        className={clsx(buttonVariants({ variant, size, className }))}
        ref={ref}
        disabled={disabled || loading}
        {...props}
      >
        {loading ? (
          <>
            <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
            Loading...
          </>
        ) : (
          <>
            {leftIcon && <span className="mr-2">{leftIcon}</span>}
            {children}
            {rightIcon && <span className="ml-2">{rightIcon}</span>}
          </>
        )}
      </button>
    )
  }
)

Button.displayName = 'Button'

export { Button, buttonVariants }