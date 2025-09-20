import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import { DndContext } from '@dnd-kit/core'
import { TodoItem } from '../../src/components/features/TodoItem'
import { TodoItemResponse, TodoPriority } from '../../src/lib/api/types'

// Mock the drag and drop functionality
jest.mock('@dnd-kit/sortable', () => ({
  useSortable: () => ({
    attributes: {},
    listeners: {},
    setNodeRef: jest.fn(),
    transform: null,
    transition: null,
    isDragging: false,
  }),
}))

const mockTodo: TodoItemResponse = {
  id: '123e4567-e89b-12d3-a456-426614174000',
  title: 'Test TODO',
  description: 'Test description',
  completed: false,
  completed_at: undefined,
  priority: 'medium' as TodoPriority,
  order_index: 0,
  created_at: '2025-01-19T10:30:00Z',
  updated_at: '2025-01-19T10:30:00Z',
}

const mockCompletedTodo: TodoItemResponse = {
  ...mockTodo,
  id: '987fcdeb-51a2-43d7-b456-789012345678',
  title: 'Completed TODO',
  completed: true,
  completed_at: '2025-01-19T15:00:00Z',
}

describe('TodoItem Component', () => {
  const mockOnUpdate = jest.fn()
  const mockOnDelete = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders todo item correctly', () => {
    render(
      <TodoItem
        todo={mockTodo}
        onUpdate={mockOnUpdate}
        onDelete={mockOnDelete}
      />
    )

    expect(screen.getByText('Test TODO')).toBeInTheDocument()
    expect(screen.getByText('Test description')).toBeInTheDocument()
    expect(screen.getByText('Medium')).toBeInTheDocument()
  })

  it('renders completed todo with different styling', () => {
    render(
      <TodoItem
        todo={mockCompletedTodo}
        onUpdate={mockOnUpdate}
        onDelete={mockOnDelete}
      />
    )

    const title = screen.getByText('Completed TODO')
    expect(title).toHaveClass('line-through')

    const checkbox = screen.getByRole('button', { name: /mark as incomplete/i })
    expect(checkbox).toHaveClass('bg-cyan-500')
  })

  it('toggles completion status when checkbox is clicked', () => {
    render(
      <TodoItem
        todo={mockTodo}
        onUpdate={mockOnUpdate}
        onDelete={mockOnDelete}
      />
    )

    const checkbox = screen.getByRole('button', { name: /mark as complete/i })
    fireEvent.click(checkbox)

    expect(mockOnUpdate).toHaveBeenCalledWith({
      id: mockTodo.id,
      completed: true,
      completed_at: expect.any(String),
    })
  })

  it('enters edit mode when edit button is clicked', () => {
    render(
      <TodoItem
        todo={mockTodo}
        onUpdate={mockOnUpdate}
        onDelete={mockOnDelete}
      />
    )

    // Actions should be visible on hover, but for testing we'll find the edit button
    const editButton = screen.getByRole('button', { name: /edit todo/i })
    fireEvent.click(editButton)

    // Should show input fields
    expect(screen.getByDisplayValue('Test TODO')).toBeInTheDocument()
    expect(screen.getByDisplayValue('Test description')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /save/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument()
  })

  it('saves changes when save button is clicked', async () => {
    render(
      <TodoItem
        todo={mockTodo}
        onUpdate={mockOnUpdate}
        onDelete={mockOnDelete}
      />
    )

    // Enter edit mode
    const editButton = screen.getByRole('button', { name: /edit todo/i })
    fireEvent.click(editButton)

    // Modify the title
    const titleInput = screen.getByDisplayValue('Test TODO')
    fireEvent.change(titleInput, { target: { value: 'Updated TODO' } })

    // Select high priority
    const prioritySelect = screen.getByRole('combobox')
    fireEvent.change(prioritySelect, { target: { value: 'high' } })

    // Save changes
    const saveButton = screen.getByRole('button', { name: /save/i })
    fireEvent.click(saveButton)

    expect(mockOnUpdate).toHaveBeenCalledWith({
      id: mockTodo.id,
      title: 'Updated TODO',
      description: 'Test description',
      priority: 'high',
    })
  })

  it('cancels edit mode when cancel button is clicked', () => {
    render(
      <TodoItem
        todo={mockTodo}
        onUpdate={mockOnUpdate}
        onDelete={mockOnDelete}
      />
    )

    // Enter edit mode
    const editButton = screen.getByRole('button', { name: /edit todo/i })
    fireEvent.click(editButton)

    // Modify the title
    const titleInput = screen.getByDisplayValue('Test TODO')
    fireEvent.change(titleInput, { target: { value: 'Should be canceled' } })

    // Cancel changes
    const cancelButton = screen.getByRole('button', { name: /cancel/i })
    fireEvent.click(cancelButton)

    // Should show original title again
    expect(screen.getByText('Test TODO')).toBeInTheDocument()
    expect(screen.queryByDisplayValue('Should be canceled')).not.toBeInTheDocument()
  })

  it('does not save empty title', () => {
    render(
      <TodoItem
        todo={mockTodo}
        onUpdate={mockOnUpdate}
        onDelete={mockOnDelete}
      />
    )

    // Enter edit mode
    const editButton = screen.getByRole('button', { name: /edit todo/i })
    fireEvent.click(editButton)

    // Clear the title
    const titleInput = screen.getByDisplayValue('Test TODO')
    fireEvent.change(titleInput, { target: { value: '' } })

    // Try to save
    const saveButton = screen.getByRole('button', { name: /save/i })
    fireEvent.click(saveButton)

    // Should not call onUpdate and should stay in edit mode
    expect(mockOnUpdate).not.toHaveBeenCalled()
    expect(screen.getByRole('button', { name: /save/i })).toBeInTheDocument()
  })

  it('shows delete confirmation and deletes todo', () => {
    // Mock window.confirm
    const confirmSpy = jest.spyOn(window, 'confirm').mockReturnValue(true)

    render(
      <TodoItem
        todo={mockTodo}
        onUpdate={mockOnUpdate}
        onDelete={mockOnDelete}
      />
    )

    const deleteButton = screen.getByRole('button', { name: /delete todo/i })
    fireEvent.click(deleteButton)

    expect(confirmSpy).toHaveBeenCalledWith('Are you sure you want to delete this TODO?')
    expect(mockOnDelete).toHaveBeenCalledWith(mockTodo.id)

    confirmSpy.mockRestore()
  })

  it('does not delete todo when confirmation is cancelled', () => {
    // Mock window.confirm to return false
    const confirmSpy = jest.spyOn(window, 'confirm').mockReturnValue(false)

    render(
      <TodoItem
        todo={mockTodo}
        onUpdate={mockOnUpdate}
        onDelete={mockOnDelete}
      />
    )

    const deleteButton = screen.getByRole('button', { name: /delete todo/i })
    fireEvent.click(deleteButton)

    expect(confirmSpy).toHaveBeenCalled()
    expect(mockOnDelete).not.toHaveBeenCalled()

    confirmSpy.mockRestore()
  })

  it('renders drag handle when dragHandle prop is true', () => {
    render(
      <DndContext onDragEnd={() => {}}>
        <TodoItem
          todo={mockTodo}
          onUpdate={mockOnUpdate}
          onDelete={mockOnDelete}
          dragHandle={true}
        />
      </DndContext>
    )

    const dragHandle = screen.getByRole('button', { name: /drag to reorder/i })
    expect(dragHandle).toBeInTheDocument()
  })

  it('does not render drag handle when dragHandle prop is false', () => {
    render(
      <TodoItem
        todo={mockTodo}
        onUpdate={mockOnUpdate}
        onDelete={mockOnDelete}
        dragHandle={false}
      />
    )

    const dragHandle = screen.queryByRole('button', { name: /drag to reorder/i })
    expect(dragHandle).not.toBeInTheDocument()
  })

  it('displays priority colors correctly', () => {
    const { rerender } = render(
      <TodoItem
        todo={{ ...mockTodo, priority: 'high' as TodoPriority }}
        onUpdate={mockOnUpdate}
        onDelete={mockOnDelete}
      />
    )

    expect(screen.getByText('High')).toHaveClass('text-red-400')

    rerender(
      <TodoItem
        todo={{ ...mockTodo, priority: 'low' as TodoPriority }}
        onUpdate={mockOnUpdate}
        onDelete={mockOnDelete}
      />
    )

    expect(screen.getByText('Low')).toHaveClass('text-green-400')
  })

  it('shows creation and completion dates', () => {
    render(
      <TodoItem
        todo={mockCompletedTodo}
        onUpdate={mockOnUpdate}
        onDelete={mockOnDelete}
      />
    )

    expect(screen.getByText(/Created/)).toBeInTheDocument()
    expect(screen.getByText(/Completed \d/)).toBeInTheDocument()
  })

  it('handles todos without description', () => {
    const todoWithoutDescription = { ...mockTodo, description: undefined }

    render(
      <TodoItem
        todo={todoWithoutDescription}
        onUpdate={mockOnUpdate}
        onDelete={mockOnDelete}
      />
    )

    expect(screen.getByText('Test TODO')).toBeInTheDocument()
    expect(screen.queryByText('Test description')).not.toBeInTheDocument()
  })

  it('applies cyberpunk styling classes', () => {
    const { container } = render(
      <TodoItem
        todo={mockTodo}
        onUpdate={mockOnUpdate}
        onDelete={mockOnDelete}
      />
    )

    // Check for cyberpunk card styling
    const card = container.querySelector('.border-cyan-500')
    expect(card).toBeInTheDocument()
  })
})