import { useState } from 'react'
import { Pencil, Trash2, Check, X, ChevronUp, ChevronDown, GripVertical } from 'lucide-react'
import { Button, Card } from '../ui'
import { TodoItemResponse, TodoPriority } from '../../lib/api/types'
import { clsx } from 'clsx'
import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'

interface TodoItemProps {
  todo: TodoItemResponse
  onUpdate: (todo: Partial<TodoItemResponse> & { id: string }) => void
  onDelete: (id: string) => void
  dragHandle?: boolean
}

const priorityColors = {
  low: 'text-green-400 border-green-500',
  medium: 'text-yellow-400 border-yellow-500',
  high: 'text-red-400 border-red-500',
}

const priorityLabels = {
  low: 'Low',
  medium: 'Medium',
  high: 'High',
}

export function TodoItem({ todo, onUpdate, onDelete, dragHandle = false }: TodoItemProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [editTitle, setEditTitle] = useState(todo.title)
  const [editDescription, setEditDescription] = useState(todo.description || '')
  const [editPriority, setEditPriority] = useState<TodoPriority>(todo.priority)

  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({
    id: todo.id,
  })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  }

  const handleToggleComplete = () => {
    onUpdate({
      id: todo.id,
      completed: !todo.completed,
      completed_at: !todo.completed ? new Date().toISOString() : undefined,
    })
  }

  const handleSaveEdit = () => {
    if (editTitle.trim()) {
      onUpdate({
        id: todo.id,
        title: editTitle.trim(),
        description: editDescription.trim() || undefined,
        priority: editPriority,
      })
      setIsEditing(false)
    }
  }

  const handleCancelEdit = () => {
    setEditTitle(todo.title)
    setEditDescription(todo.description || '')
    setEditPriority(todo.priority)
    setIsEditing(false)
  }

  const handleDelete = () => {
    if (window.confirm('Are you sure you want to delete this TODO?')) {
      onDelete(todo.id)
    }
  }

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={clsx(
        'transition-all duration-200',
        isDragging && 'opacity-50 scale-105'
      )}
    >
      <Card
        className={clsx(
          'group transition-all duration-300 hover:border-cyan-400',
          todo.completed && 'opacity-70 bg-gray-800/40',
          isEditing && 'border-purple-500 shadow-neon'
        )}
        hover={!isDragging}
      >
        <div className="flex items-start gap-3">
          {/* Drag Handle */}
          {dragHandle && (
            <button
              {...attributes}
              {...listeners}
              className="mt-1 text-cyan-400 hover:text-cyan-300 opacity-0 group-hover:opacity-100 transition-opacity duration-200 cursor-grab active:cursor-grabbing"
              aria-label="Drag to reorder"
            >
              <GripVertical className="h-4 w-4" />
            </button>
          )}

          {/* Completion Checkbox */}
          <button
            onClick={handleToggleComplete}
            className={clsx(
              'mt-1 flex h-5 w-5 items-center justify-center rounded border-2 transition-all duration-200',
              todo.completed
                ? 'bg-cyan-500 border-cyan-500 text-black'
                : 'border-cyan-500 hover:border-cyan-400 hover:bg-cyan-500/10'
            )}
            aria-label={todo.completed ? 'Mark as incomplete' : 'Mark as complete'}
          >
            {todo.completed && <Check className="h-3 w-3" />}
          </button>

          {/* Content */}
          <div className="flex-1 min-w-0">
            {isEditing ? (
              <div className="space-y-3">
                <input
                  type="text"
                  value={editTitle}
                  onChange={(e) => setEditTitle(e.target.value)}
                  className="w-full bg-gray-800 border border-cyan-500 rounded px-3 py-2 text-cyan-100 placeholder-cyan-400 font-mono focus:border-cyan-300 focus:ring-2 focus:ring-cyan-500 focus:ring-opacity-50"
                  placeholder="Enter TODO title..."
                  autoFocus
                />
                <textarea
                  value={editDescription}
                  onChange={(e) => setEditDescription(e.target.value)}
                  className="w-full bg-gray-800 border border-cyan-500 rounded px-3 py-2 text-cyan-100 placeholder-cyan-400 font-mono focus:border-cyan-300 focus:ring-2 focus:ring-cyan-500 focus:ring-opacity-50 resize-none"
                  placeholder="Enter description (optional)..."
                  rows={2}
                />
                <select
                  value={editPriority}
                  onChange={(e) => setEditPriority(e.target.value as TodoPriority)}
                  className="bg-gray-800 border border-cyan-500 rounded px-3 py-2 text-cyan-100 font-mono focus:border-cyan-300 focus:ring-2 focus:ring-cyan-500 focus:ring-opacity-50"
                >
                  <option value="low">Low Priority</option>
                  <option value="medium">Medium Priority</option>
                  <option value="high">High Priority</option>
                </select>
                <div className="flex gap-2">
                  <Button size="sm" onClick={handleSaveEdit}>
                    <Check className="h-3 w-3" />
                    Save
                  </Button>
                  <Button variant="secondary" size="sm" onClick={handleCancelEdit}>
                    <X className="h-3 w-3" />
                    Cancel
                  </Button>
                </div>
              </div>
            ) : (
              <div className="space-y-2">
                <div className="flex items-start justify-between gap-2">
                  <h3
                    className={clsx(
                      'font-mono text-sm font-medium transition-all duration-200',
                      todo.completed
                        ? 'text-cyan-400/70 line-through'
                        : 'text-cyan-100 group-hover:text-cyan-300'
                    )}
                  >
                    {todo.title}
                  </h3>
                  <div className="flex items-center gap-1">
                    {/* Priority Indicator */}
                    <span
                      className={clsx(
                        'px-2 py-1 text-xs font-mono rounded border',
                        priorityColors[todo.priority]
                      )}
                    >
                      {priorityLabels[todo.priority]}
                    </span>
                  </div>
                </div>

                {todo.description && (
                  <p
                    className={clsx(
                      'text-sm font-mono text-cyan-400/80 transition-all duration-200',
                      todo.completed && 'line-through opacity-50'
                    )}
                  >
                    {todo.description}
                  </p>
                )}

                <div className="flex items-center justify-between text-xs text-cyan-400/60 font-mono">
                  <span>
                    Created {new Date(todo.created_at).toLocaleDateString()}
                  </span>
                  {todo.completed && todo.completed_at && (
                    <span>
                      Completed {new Date(todo.completed_at).toLocaleDateString()}
                    </span>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Actions */}
          {!isEditing && (
            <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setIsEditing(true)}
                className="h-8 w-8 text-cyan-400 hover:text-cyan-300"
                aria-label="Edit TODO"
              >
                <Pencil className="h-3 w-3" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                onClick={handleDelete}
                className="h-8 w-8 text-red-400 hover:text-red-300"
                aria-label="Delete TODO"
              >
                <Trash2 className="h-3 w-3" />
              </Button>
            </div>
          )}
        </div>
      </Card>
    </div>
  )
}