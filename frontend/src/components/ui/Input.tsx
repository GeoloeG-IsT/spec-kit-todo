import { InputHTMLAttributes, forwardRef, useId } from 'react'
import { clsx } from 'clsx'

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
  helperText?: string
  leftIcon?: React.ReactNode
  rightIcon?: React.ReactNode
}

const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, label, error, helperText, leftIcon, rightIcon, id, ...props }, ref) => {
    const generatedId = useId()
    const inputId = id || generatedId

    return (
      <div className="w-full">
        {label && (
          <label
            htmlFor={inputId}
            className="block text-sm font-medium text-cyan-300 mb-2 font-mono"
          >
            {label}
          </label>
        )}
        <div className="relative">
          {leftIcon && (
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <span className="text-cyan-400">{leftIcon}</span>
            </div>
          )}
          <input
            type={type}
            className={clsx(
              'block w-full rounded-md bg-gray-800 border text-cyan-100 placeholder-cyan-400 font-mono',
              'focus:ring-2 focus:ring-opacity-50 transition-all duration-200',
              'disabled:cursor-not-allowed disabled:opacity-50',
              leftIcon ? 'pl-10' : 'pl-3',
              rightIcon ? 'pr-10' : 'pr-3',
              'py-2',
              error
                ? 'border-red-500 text-red-400 focus:border-red-400 focus:ring-red-500'
                : 'border-cyan-500 focus:border-cyan-300 focus:ring-cyan-500',
              className
            )}
            style={{
              boxShadow: error
                ? 'focus:0 0 0 2px rgba(239, 68, 68, 0.2), 0 0 10px rgba(239, 68, 68, 0.3)'
                : 'focus:0 0 0 2px rgba(0, 255, 255, 0.2), 0 0 10px rgba(0, 255, 255, 0.3)'
            }}
            ref={ref}
            id={inputId}
            {...props}
          />
          {rightIcon && (
            <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
              <span className="text-cyan-400">{rightIcon}</span>
            </div>
          )}
        </div>
        {error && (
          <p className="mt-1 text-sm text-red-400 font-mono fade-in">
            {error}
          </p>
        )}
        {helperText && !error && (
          <p className="mt-1 text-sm text-cyan-400 opacity-70 font-mono">
            {helperText}
          </p>
        )}
      </div>
    )
  }
)

Input.displayName = 'Input'

export { Input }