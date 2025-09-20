import { HTMLAttributes, forwardRef } from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { clsx } from 'clsx'

const cardVariants = cva(
  'rounded-lg border backdrop-blur-sm relative overflow-hidden transition-all duration-300',
  {
    variants: {
      variant: {
        default: 'bg-gray-900 bg-opacity-80 border-cyan-500 shadow-lg hover:shadow-neon-sm',
        muted: 'bg-gray-800 bg-opacity-60 border-gray-600 shadow-md',
        danger: 'bg-red-900 bg-opacity-20 border-red-500 shadow-lg hover:shadow-red-500/20',
        success: 'bg-green-900 bg-opacity-20 border-green-500 shadow-lg hover:shadow-green-500/20',
        transparent: 'bg-transparent border-cyan-500 border-opacity-30',
      },
      size: {
        sm: 'p-3',
        md: 'p-4',
        lg: 'p-6',
        xl: 'p-8',
      },
      glow: {
        none: '',
        subtle: 'hover:shadow-neon-sm',
        normal: 'shadow-neon-sm hover:shadow-neon',
        intense: 'shadow-neon hover:shadow-neon animate-pulse-neon',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'md',
      glow: 'none',
    },
  }
)

export interface CardProps
  extends HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof cardVariants> {
  hover?: boolean
}

const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ className, variant, size, glow, hover = true, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={clsx(
          cardVariants({ variant, size, glow }),
          hover && 'hover:scale-[1.02] hover:border-cyan-400',
          className
        )}
        {...props}
      >
        {/* Holographic overlay effect */}
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-cyan-500/10 to-transparent opacity-0 hover:opacity-100 transition-opacity duration-300 pointer-events-none" />
        <div className="relative z-10">
          {children}
        </div>
      </div>
    )
  }
)

Card.displayName = 'Card'

const CardHeader = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={clsx('flex flex-col space-y-1.5 pb-4 border-b border-cyan-500/20', className)}
      {...props}
    />
  )
)

CardHeader.displayName = 'CardHeader'

const CardTitle = forwardRef<HTMLParagraphElement, HTMLAttributes<HTMLHeadingElement>>(
  ({ className, ...props }, ref) => (
    <h3
      ref={ref}
      className={clsx('text-lg font-semibold leading-none tracking-tight text-cyan-300 font-mono neon-text', className)}
      {...props}
    />
  )
)

CardTitle.displayName = 'CardTitle'

const CardDescription = forwardRef<HTMLParagraphElement, HTMLAttributes<HTMLParagraphElement>>(
  ({ className, ...props }, ref) => (
    <p
      ref={ref}
      className={clsx('text-sm text-cyan-400 opacity-80 font-mono', className)}
      {...props}
    />
  )
)

CardDescription.displayName = 'CardDescription'

const CardContent = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={clsx('pt-4', className)}
      {...props}
    />
  )
)

CardContent.displayName = 'CardContent'

const CardFooter = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={clsx('flex items-center pt-4 border-t border-cyan-500/20', className)}
      {...props}
    />
  )
)

CardFooter.displayName = 'CardFooter'

export { Card, CardHeader, CardFooter, CardTitle, CardDescription, CardContent }