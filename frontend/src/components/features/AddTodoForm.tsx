import { useState } from 'react'
import { Plus, Sparkles } from 'lucide-react'
import { Button, Card, Input } from '../ui'
import { TodoItemCreate, TodoPriority } from '../../lib/api/types'
import { clsx } from 'clsx'

interface AddTodoFormProps {
  onAddTodo: (todo: TodoItemCreate) => void
  loading?: boolean
  className?: string
}

export function AddTodoForm({ onAddTodo, loading = false, className }: AddTodoFormProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [priority, setPriority] = useState<TodoPriority>('medium')
  const [titleError, setTitleError] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    if (!title.trim()) {
      setTitleError('Title is required')
      return
    }

    if (title.length > 2000) {
      setTitleError('Title must be 2000 characters or less')
      return
    }

    if (description.length > 10000) {
      return
    }

    const newTodo: TodoItemCreate = {
      title: title.trim(),
      description: description.trim() || undefined,
      priority,
    }

    onAddTodo(newTodo)

    // Reset form
    setTitle('')
    setDescription('')
    setPriority('medium')
    setTitleError('')
    setIsExpanded(false)
  }

  const handleCancel = () => {
    setTitle('')
    setDescription('')
    setPriority('medium')
    setTitleError('')
    setIsExpanded(false)
  }

  const priorityOptions = [
    { value: 'low', label: 'Low Priority', color: 'text-green-400 border-green-500' },
    { value: 'medium', label: 'Medium Priority', color: 'text-yellow-400 border-yellow-500' },
    { value: 'high', label: 'High Priority', color: 'text-red-400 border-red-500' },
  ]

  return (
    <Card className={clsx('transition-all duration-300', className)} glow="subtle">
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Quick Add Input */}
        <div className="flex gap-3">
          <div className="flex-1">
            <Input
              type="text"
              placeholder={isExpanded ? "Enter TODO title..." : "What needs to be done?"}
              value={title}
              onChange={(e) => {
                setTitle(e.target.value)
                setTitleError('')
              }}
              onFocus={() => setIsExpanded(true)}
              error={titleError}
              leftIcon={<Sparkles className="h-4 w-4" />}
              maxLength={2000}
            />
          </div>
          {!isExpanded && (
            <Button
              type="button"
              onClick={() => setIsExpanded(true)}
              className="shrink-0"
            >
              <Plus className="h-4 w-4" />
              Add
            </Button>
          )}
        </div>

        {/* Character count for title */}
        {title && (
          <div className="text-xs text-cyan-400/70 font-mono text-right">
            {title.length}/2000 characters
          </div>
        )}

        {/* Expanded Form */}
        {isExpanded && (
          <div className="space-y-4 animate-fade-in">
            {/* Description */}
            <div>
              <label className="block text-sm font-medium text-cyan-300 mb-2 font-mono">
                Description (optional)
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Add more details about this TODO..."
                className="w-full bg-gray-800 border border-cyan-500 rounded px-3 py-2 text-cyan-100 placeholder-cyan-400 font-mono focus:border-cyan-300 focus:ring-2 focus:ring-cyan-500 focus:ring-opacity-50 resize-none transition-all duration-200"
                rows={3}
                maxLength={10000}
              />
              {description && (
                <div className="text-xs text-cyan-400/70 font-mono text-right mt-1">
                  {description.length}/10000 characters
                </div>
              )}
            </div>

            {/* Priority Selection */}
            <div>
              <label className="block text-sm font-medium text-cyan-300 mb-2 font-mono">
                Priority
              </label>
              <div className="grid grid-cols-3 gap-2">
                {priorityOptions.map((option) => (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => setPriority(option.value as TodoPriority)}
                    className={clsx(
                      'px-3 py-2 text-sm font-mono rounded border-2 transition-all duration-200',
                      'hover:bg-opacity-20 hover:scale-105',
                      priority === option.value
                        ? `${option.color} bg-current bg-opacity-20 shadow-neon-sm`
                        : 'text-cyan-400 border-cyan-500 hover:border-cyan-400'
                    )}
                  >
                    {option.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Form Actions */}
            <div className="flex gap-3 pt-2 border-t border-cyan-500/20">
              <Button
                type="submit"
                loading={loading}
                className="flex-1"
                disabled={!title.trim() || loading}
              >
                <Plus className="h-4 w-4" />
                {loading ? 'Adding...' : 'Add TODO'}
              </Button>
              <Button
                type="button"
                variant="secondary"
                onClick={handleCancel}
                disabled={loading}
              >
                Cancel
              </Button>
            </div>
          </div>
        )}
      </form>
    </Card>
  )
}