import { render, screen, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import { Button } from '../../src/components/ui/Button'

describe('Button Component', () => {
  it('renders with default props', () => {
    render(<Button>Click me</Button>)

    const button = screen.getByRole('button', { name: /click me/i })
    expect(button).toBeInTheDocument()
    expect(button).toHaveClass('bg-cyan-500')
  })

  it('renders different variants correctly', () => {
    const { rerender } = render(<Button variant="secondary">Secondary</Button>)

    let button = screen.getByRole('button')
    expect(button).toHaveClass('bg-transparent', 'text-purple-400')

    rerender(<Button variant="danger">Danger</Button>)
    button = screen.getByRole('button')
    expect(button).toHaveClass('text-red-400')

    rerender(<Button variant="ghost">Ghost</Button>)
    button = screen.getByRole('button')
    expect(button).toHaveClass('text-cyan-400')
  })

  it('renders different sizes correctly', () => {
    const { rerender } = render(<Button size="sm">Small</Button>)

    let button = screen.getByRole('button')
    expect(button).toHaveClass('h-8', 'px-3')

    rerender(<Button size="lg">Large</Button>)
    button = screen.getByRole('button')
    expect(button).toHaveClass('h-12', 'px-8')

    rerender(<Button size="icon">Icon</Button>)
    button = screen.getByRole('button')
    expect(button).toHaveClass('h-10', 'w-10')
  })

  it('shows loading state correctly', () => {
    render(<Button loading>Loading</Button>)

    const button = screen.getByRole('button')
    expect(button).toBeDisabled()
    expect(button).toHaveTextContent('Loading...')

    // Check for loading spinner
    const spinner = button.querySelector('.animate-spin')
    expect(spinner).toBeInTheDocument()
  })

  it('handles click events', () => {
    const handleClick = jest.fn()
    render(<Button onClick={handleClick}>Click me</Button>)

    const button = screen.getByRole('button')
    fireEvent.click(button)

    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('is disabled when disabled prop is true', () => {
    render(<Button disabled>Disabled</Button>)

    const button = screen.getByRole('button')
    expect(button).toBeDisabled()
  })

  it('is disabled when loading is true', () => {
    render(<Button loading>Loading</Button>)

    const button = screen.getByRole('button')
    expect(button).toBeDisabled()
  })

  it('renders with left and right icons', () => {
    const LeftIcon = () => <span data-testid="left-icon">←</span>
    const RightIcon = () => <span data-testid="right-icon">→</span>

    render(
      <Button leftIcon={<LeftIcon />} rightIcon={<RightIcon />}>
        With Icons
      </Button>
    )

    expect(screen.getByTestId('left-icon')).toBeInTheDocument()
    expect(screen.getByTestId('right-icon')).toBeInTheDocument()
  })

  it('applies custom className', () => {
    render(<Button className="custom-class">Custom</Button>)

    const button = screen.getByRole('button')
    expect(button).toHaveClass('custom-class')
  })

  it('forwards ref correctly', () => {
    const ref = jest.fn()
    render(<Button ref={ref}>Ref test</Button>)

    expect(ref).toHaveBeenCalled()
  })

  it('does not show icons when loading', () => {
    const LeftIcon = () => <span data-testid="left-icon">←</span>

    render(
      <Button loading leftIcon={<LeftIcon />}>
        Loading
      </Button>
    )

    expect(screen.queryByTestId('left-icon')).not.toBeInTheDocument()
    expect(screen.getByText('Loading...')).toBeInTheDocument()
  })

  it('maintains cyberpunk styling classes', () => {
    render(<Button>Cyberpunk</Button>)

    const button = screen.getByRole('button')
    expect(button).toHaveClass('font-mono', 'glitch-hover', 'transform', 'hover:scale-105')
  })
})