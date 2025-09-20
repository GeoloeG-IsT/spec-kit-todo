import { test, expect } from '@playwright/test'

test.describe('Guest User Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('networkidle')
  })

  test('1. Guest user can access the TODO list without authentication', async ({ page }) => {
    // Check that the page loads and shows the TODO interface
    await expect(page).toHaveTitle(/TODO/)

    // Check for main elements
    await expect(page.getByRole('heading', { name: /TODOs/i })).toBeVisible()
    await expect(page.getByPlaceholder(/What needs to be done/i)).toBeVisible()

    // Check that no sign-in prompt is blocking access
    const addButton = page.getByRole('button', { name: /Add TODO/i })
    await expect(addButton).toBeVisible()
  })

  test('2. Guest user can add TODOs with real-time updates', async ({ page }) => {
    const todoTitle = 'Test guest TODO ' + Date.now()
    const todoDescription = 'This is a test description'

    // Add a new TODO
    await page.getByPlaceholder(/What needs to be done/i).fill(todoTitle)
    await page.getByPlaceholder(/Add a description/i).fill(todoDescription)
    await page.getByRole('button', { name: /Add TODO/i }).click()

    // Check that the TODO appears in the list
    const todoItem = page.locator('[data-testid="todo-item"]').filter({ hasText: todoTitle })
    await expect(todoItem).toBeVisible()
    await expect(todoItem).toContainText(todoDescription)

    // Check priority indicator
    await expect(todoItem.locator('[data-testid="priority-badge"]')).toContainText(/Medium/i)
  })

  test('3. Guest user can edit existing TODOs', async ({ page }) => {
    // First add a TODO
    const originalTitle = 'Original TODO ' + Date.now()
    await page.getByPlaceholder(/What needs to be done/i).fill(originalTitle)
    await page.getByRole('button', { name: /Add TODO/i }).click()

    // Wait for TODO to appear
    const todoItem = page.locator('[data-testid="todo-item"]').filter({ hasText: originalTitle })
    await expect(todoItem).toBeVisible()

    // Edit the TODO
    await todoItem.hover()
    await todoItem.getByRole('button', { name: /Edit/i }).click()

    const newTitle = 'Updated TODO ' + Date.now()
    await todoItem.getByRole('textbox').first().clear()
    await todoItem.getByRole('textbox').first().fill(newTitle)
    await todoItem.getByRole('button', { name: /Save/i }).click()

    // Check that the TODO is updated
    await expect(page.locator('[data-testid="todo-item"]').filter({ hasText: newTitle })).toBeVisible()
    await expect(page.locator('[data-testid="todo-item"]').filter({ hasText: originalTitle })).not.toBeVisible()
  })

  test('4. Guest user can mark TODOs as complete/incomplete', async ({ page }) => {
    // Add a TODO
    const todoTitle = 'Complete test TODO ' + Date.now()
    await page.getByPlaceholder(/What needs to be done/i).fill(todoTitle)
    await page.getByRole('button', { name: /Add TODO/i }).click()

    const todoItem = page.locator('[data-testid="todo-item"]').filter({ hasText: todoTitle })
    await expect(todoItem).toBeVisible()

    // Mark as complete
    const checkbox = todoItem.locator('[data-testid="todo-checkbox"]')
    await checkbox.click()

    // Check that TODO is marked as complete
    await expect(todoItem).toHaveClass(/completed/)
    await expect(todoItem.locator('h3')).toHaveCSS('text-decoration', /line-through/)

    // Mark as incomplete
    await checkbox.click()

    // Check that TODO is no longer complete
    await expect(todoItem).not.toHaveClass(/completed/)
    await expect(todoItem.locator('h3')).not.toHaveCSS('text-decoration', /line-through/)
  })

  test('5. Guest user can delete TODOs', async ({ page }) => {
    // Add a TODO to delete
    const todoTitle = 'Delete test TODO ' + Date.now()
    await page.getByPlaceholder(/What needs to be done/i).fill(todoTitle)
    await page.getByRole('button', { name: /Add TODO/i }).click()

    const todoItem = page.locator('[data-testid="todo-item"]').filter({ hasText: todoTitle })
    await expect(todoItem).toBeVisible()

    // Delete the TODO
    await todoItem.hover()

    // Handle the confirmation dialog
    page.on('dialog', dialog => dialog.accept())
    await todoItem.getByRole('button', { name: /Delete/i }).click()

    // Check that the TODO is removed
    await expect(todoItem).not.toBeVisible()
  })

  test('6. Guest user can filter TODOs by status', async ({ page }) => {
    // Add multiple TODOs with different statuses
    const todo1 = 'Active TODO ' + Date.now()
    const todo2 = 'Completed TODO ' + Date.now()

    // Add first TODO
    await page.getByPlaceholder(/What needs to be done/i).fill(todo1)
    await page.getByRole('button', { name: /Add TODO/i }).click()

    // Add second TODO
    await page.getByPlaceholder(/What needs to be done/i).fill(todo2)
    await page.getByRole('button', { name: /Add TODO/i }).click()

    // Mark second TODO as complete
    const todoItem2 = page.locator('[data-testid="todo-item"]').filter({ hasText: todo2 })
    await todoItem2.locator('[data-testid="todo-checkbox"]').click()

    // Filter to show only active TODOs
    await page.getByRole('button', { name: /Active/i }).click()
    await expect(page.locator('[data-testid="todo-item"]').filter({ hasText: todo1 })).toBeVisible()
    await expect(page.locator('[data-testid="todo-item"]').filter({ hasText: todo2 })).not.toBeVisible()

    // Filter to show only completed TODOs
    await page.getByRole('button', { name: /Completed/i }).click()
    await expect(page.locator('[data-testid="todo-item"]').filter({ hasText: todo1 })).not.toBeVisible()
    await expect(page.locator('[data-testid="todo-item"]').filter({ hasText: todo2 })).toBeVisible()

    // Show all TODOs
    await page.getByRole('button', { name: /All/i }).click()
    await expect(page.locator('[data-testid="todo-item"]').filter({ hasText: todo1 })).toBeVisible()
    await expect(page.locator('[data-testid="todo-item"]').filter({ hasText: todo2 })).toBeVisible()
  })

  test('7. Guest user can set TODO priorities', async ({ page }) => {
    const todoTitle = 'Priority test TODO ' + Date.now()

    // Add TODO with high priority
    await page.getByPlaceholder(/What needs to be done/i).fill(todoTitle)
    await page.getByRole('combobox', { name: /Priority/i }).selectOption('high')
    await page.getByRole('button', { name: /Add TODO/i }).click()

    const todoItem = page.locator('[data-testid="todo-item"]').filter({ hasText: todoTitle })
    await expect(todoItem).toBeVisible()

    // Check that high priority is displayed
    await expect(todoItem.locator('[data-testid="priority-badge"]')).toContainText(/High/i)
    await expect(todoItem.locator('[data-testid="priority-badge"]')).toHaveClass(/high-priority/)

    // Edit to change priority
    await todoItem.hover()
    await todoItem.getByRole('button', { name: /Edit/i }).click()
    await todoItem.getByRole('combobox').selectOption('low')
    await todoItem.getByRole('button', { name: /Save/i }).click()

    // Check that priority is updated
    await expect(todoItem.locator('[data-testid="priority-badge"]')).toContainText(/Low/i)
    await expect(todoItem.locator('[data-testid="priority-badge"]')).toHaveClass(/low-priority/)
  })

  test('8. Guest user session persists across page refreshes', async ({ page }) => {
    // Add a TODO
    const todoTitle = 'Persistent TODO ' + Date.now()
    const todoDescription = 'This should persist'

    await page.getByPlaceholder(/What needs to be done/i).fill(todoTitle)
    await page.getByPlaceholder(/Add a description/i).fill(todoDescription)
    await page.getByRole('button', { name: /Add TODO/i }).click()

    // Wait for TODO to appear
    await expect(page.locator('[data-testid="todo-item"]').filter({ hasText: todoTitle })).toBeVisible()

    // Reload the page
    await page.reload()
    await page.waitForLoadState('networkidle')

    // Check that the TODO is still there
    const todoItem = page.locator('[data-testid="todo-item"]').filter({ hasText: todoTitle })
    await expect(todoItem).toBeVisible()
    await expect(todoItem).toContainText(todoDescription)

    // Mark it as complete
    await todoItem.locator('[data-testid="todo-checkbox"]').click()
    await expect(todoItem).toHaveClass(/completed/)

    // Reload again
    await page.reload()
    await page.waitForLoadState('networkidle')

    // Check that the completion status persists
    await expect(page.locator('[data-testid="todo-item"]').filter({ hasText: todoTitle })).toHaveClass(/completed/)
  })

  test('Guest user sees call-to-action to sign up', async ({ page }) => {
    // Check for sign-up CTA
    await expect(page.getByText(/Sign up to save your TODOs permanently/i)).toBeVisible()
    await expect(page.getByRole('button', { name: /Sign Up/i })).toBeVisible()

    // The sign-in button should also be available
    await expect(page.getByRole('button', { name: /Sign In/i })).toBeVisible()
  })
})