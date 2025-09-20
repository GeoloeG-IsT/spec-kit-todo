import { useState, useMemo } from 'react'
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from '@dnd-kit/core'
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable'
import {
  restrictToVerticalAxis,
  restrictToWindowEdges,
} from '@dnd-kit/modifiers'
import { Filter, SortAsc, SortDesc, Grid, List } from 'lucide-react'
import { Button, Card } from '../ui'
import { TodoItem } from './TodoItem'
import { TodoItemResponse, TodoPriority } from '../../lib/api/types'
import { clsx } from 'clsx'

interface TodoListProps {
  todos: TodoItemResponse[]
  loading?: boolean
  onUpdateTodo: (todo: Partial<TodoItemResponse> & { id: string }) => void
  onDeleteTodo: (id: string) => void
  onReorderTodos: (reorderData: Array<{ todo_id: string; order_index: number }>) => void
}

type SortOption = 'order_index' | 'created_at' | 'updated_at' | 'priority' | 'title'
type FilterOption = 'all' | 'active' | 'completed'
type ViewOption = 'list' | 'grid'

const sortLabels = {
  order_index: 'Custom Order',
  created_at: 'Date Created',
  updated_at: 'Date Modified',
  priority: 'Priority',
  title: 'Title',
}

export function TodoList({
  todos,
  loading = false,
  onUpdateTodo,
  onDeleteTodo,
  onReorderTodos,
}: TodoListProps) {
  const [filter, setFilter] = useState<FilterOption>('all')
  const [sortBy, setSortBy] = useState<SortOption>('order_index')
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc')
  const [view, setView] = useState<ViewOption>('list')
  const [priorityFilter, setPriorityFilter] = useState<TodoPriority | 'all'>('all')

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  )

  const filteredAndSortedTodos = useMemo(() => {
    let filtered = todos

    // Apply completion filter
    if (filter === 'active') {
      filtered = filtered.filter(todo => !todo.completed)
    } else if (filter === 'completed') {
      filtered = filtered.filter(todo => todo.completed)
    }

    // Apply priority filter
    if (priorityFilter !== 'all') {
      filtered = filtered.filter(todo => todo.priority === priorityFilter)
    }

    // Apply sorting
    const sorted = [...filtered].sort((a, b) => {
      let comparison = 0

      switch (sortBy) {
        case 'order_index':
          comparison = a.order_index - b.order_index
          break
        case 'created_at':
          comparison = new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
          break
        case 'updated_at':
          comparison = new Date(a.updated_at).getTime() - new Date(b.updated_at).getTime()
          break
        case 'priority':
          const priorityOrder = { high: 3, medium: 2, low: 1 }
          comparison = priorityOrder[a.priority] - priorityOrder[b.priority]
          break
        case 'title':
          comparison = a.title.toLowerCase().localeCompare(b.title.toLowerCase())
          break
      }

      return sortDirection === 'asc' ? comparison : -comparison
    })

    return sorted
  }, [todos, filter, sortBy, sortDirection, priorityFilter])

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event

    if (over && active.id !== over.id) {
      const oldIndex = filteredAndSortedTodos.findIndex(todo => todo.id === active.id)
      const newIndex = filteredAndSortedTodos.findIndex(todo => todo.id === over.id)

      const reorderedTodos = arrayMove(filteredAndSortedTodos, oldIndex, newIndex)

      // Create reorder data with new order indices
      const reorderData = reorderedTodos.map((todo, index) => ({
        todo_id: todo.id,
        order_index: index,
      }))

      onReorderTodos(reorderData)
    }
  }

  const toggleSort = (newSortBy: SortOption) => {
    if (sortBy === newSortBy) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortBy(newSortBy)
      setSortDirection('asc')
    }
  }

  const completedCount = todos.filter(todo => todo.completed).length
  const activeCount = todos.filter(todo => !todo.completed).length

  if (loading) {
    return (
      <Card className="p-8 text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-cyan-500 border-t-transparent mx-auto mb-4" />
        <p className="text-cyan-400 font-mono">Loading TODOs...</p>
      </Card>
    )
  }

  if (todos.length === 0) {
    return (
      <Card className="p-8 text-center">
        <p className="text-cyan-400 font-mono text-lg mb-2">No TODOs yet</p>
        <p className="text-cyan-400/70 font-mono text-sm">
          Create your first TODO to get started!
        </p>
      </Card>
    )
  }

  return (
    <div className="space-y-4">
      {/* Stats and Controls */}
      <Card className="p-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          {/* Stats */}
          <div className="flex items-center gap-6 text-sm font-mono">
            <span className="text-cyan-400">
              Total: <span className="text-cyan-300 font-bold">{todos.length}</span>
            </span>
            <span className="text-yellow-400">
              Active: <span className="text-yellow-300 font-bold">{activeCount}</span>
            </span>
            <span className="text-green-400">
              Completed: <span className="text-green-300 font-bold">{completedCount}</span>
            </span>
          </div>

          {/* View Toggle */}
          <div className="flex items-center gap-2">
            <Button
              variant={view === 'list' ? 'primary' : 'ghost'}
              size="sm"
              onClick={() => setView('list')}
            >
              <List className="h-4 w-4" />
            </Button>
            <Button
              variant={view === 'grid' ? 'primary' : 'ghost'}
              size="sm"
              onClick={() => setView('grid')}
            >
              <Grid className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </Card>

      {/* Filters and Sorting */}
      <Card className="p-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Filter by completion */}
          <div>
            <label className="block text-sm font-medium text-cyan-300 mb-2 font-mono">
              Status
            </label>
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value as FilterOption)}
              className="w-full bg-gray-800 border border-cyan-500 rounded px-3 py-2 text-cyan-100 font-mono focus:border-cyan-300 focus:ring-2 focus:ring-cyan-500 focus:ring-opacity-50"
            >
              <option value="all">All TODOs</option>
              <option value="active">Active</option>
              <option value="completed">Completed</option>
            </select>
          </div>

          {/* Filter by priority */}
          <div>
            <label className="block text-sm font-medium text-cyan-300 mb-2 font-mono">
              Priority
            </label>
            <select
              value={priorityFilter}
              onChange={(e) => setPriorityFilter(e.target.value as TodoPriority | 'all')}
              className="w-full bg-gray-800 border border-cyan-500 rounded px-3 py-2 text-cyan-100 font-mono focus:border-cyan-300 focus:ring-2 focus:ring-cyan-500 focus:ring-opacity-50"
            >
              <option value="all">All Priorities</option>
              <option value="high">High Priority</option>
              <option value="medium">Medium Priority</option>
              <option value="low">Low Priority</option>
            </select>
          </div>

          {/* Sort by */}
          <div>
            <label className="block text-sm font-medium text-cyan-300 mb-2 font-mono">
              Sort by
            </label>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as SortOption)}
              className="w-full bg-gray-800 border border-cyan-500 rounded px-3 py-2 text-cyan-100 font-mono focus:border-cyan-300 focus:ring-2 focus:ring-cyan-500 focus:ring-opacity-50"
            >
              {Object.entries(sortLabels).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </div>

          {/* Sort direction */}
          <div>
            <label className="block text-sm font-medium text-cyan-300 mb-2 font-mono">
              Direction
            </label>
            <Button
              variant="secondary"
              onClick={() => setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')}
              className="w-full justify-center"
            >
              {sortDirection === 'asc' ? (
                <>
                  <SortAsc className="h-4 w-4 mr-2" />
                  Ascending
                </>
              ) : (
                <>
                  <SortDesc className="h-4 w-4 mr-2" />
                  Descending
                </>
              )}
            </Button>
          </div>
        </div>
      </Card>

      {/* TODO List */}
      {filteredAndSortedTodos.length === 0 ? (
        <Card className="p-8 text-center">
          <Filter className="h-12 w-12 text-cyan-400/50 mx-auto mb-4" />
          <p className="text-cyan-400 font-mono text-lg mb-2">No TODOs match your filters</p>
          <p className="text-cyan-400/70 font-mono text-sm">
            Try adjusting your filters to see more TODOs
          </p>
        </Card>
      ) : (
        <DndContext
          sensors={sensors}
          collisionDetection={closestCenter}
          onDragEnd={handleDragEnd}
          modifiers={[restrictToVerticalAxis, restrictToWindowEdges]}
        >
          <SortableContext
            items={filteredAndSortedTodos.map(todo => todo.id)}
            strategy={verticalListSortingStrategy}
          >
            <div
              className={clsx(
                'gap-4',
                view === 'grid'
                  ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3'
                  : 'space-y-3'
              )}
            >
              {filteredAndSortedTodos.map((todo) => (
                <TodoItem
                  key={todo.id}
                  todo={todo}
                  onUpdate={onUpdateTodo}
                  onDelete={onDeleteTodo}
                  dragHandle={sortBy === 'order_index'}
                />
              ))}
            </div>
          </SortableContext>
        </DndContext>
      )}
    </div>
  )
}