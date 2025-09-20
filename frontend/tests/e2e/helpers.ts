import { Page } from '@playwright/test'

/**
 * Helper functions for E2E tests
 */

export async function mockAuthentication(page: Page, userId = 'test-user-id') {
  await page.addInitScript((userId) => {
    // Mock Clerk authentication
    window.__clerk_session = {
      id: `session-${userId}`,
      userId: userId,
      status: 'active',
    }

    localStorage.setItem('__clerk_client_jwt', `mock-jwt-${userId}`)
    localStorage.setItem('__clerk_db_jwt', `mock-db-jwt-${userId}`)
  }, userId)
}

export async function addTodo(
  page: Page,
  title: string,
  description?: string,
  priority: 'low' | 'medium' | 'high' = 'medium'
) {
  await page.getByPlaceholder(/What needs to be done/i).fill(title)

  if (description) {
    await page.getByPlaceholder(/Add a description/i).fill(description)
  }

  await page.getByRole('combobox', { name: /Priority/i }).selectOption(priority)
  await page.getByRole('button', { name: /Add TODO/i }).click()

  // Wait for TODO to appear
  await page.waitForSelector(`[data-testid="todo-item"]:has-text("${title}")`)
}

export async function markTodoComplete(page: Page, title: string) {
  const todoItem = page.locator('[data-testid="todo-item"]').filter({ hasText: title })
  await todoItem.locator('[data-testid="todo-checkbox"]').click()
}

export async function deleteTodo(page: Page, title: string) {
  const todoItem = page.locator('[data-testid="todo-item"]').filter({ hasText: title })
  await todoItem.hover()

  // Handle confirmation dialog
  page.once('dialog', dialog => dialog.accept())
  await todoItem.getByRole('button', { name: /Delete/i }).click()
}

export async function editTodo(
  page: Page,
  currentTitle: string,
  newTitle: string,
  newDescription?: string,
  newPriority?: 'low' | 'medium' | 'high'
) {
  const todoItem = page.locator('[data-testid="todo-item"]').filter({ hasText: currentTitle })
  await todoItem.hover()
  await todoItem.getByRole('button', { name: /Edit/i }).click()

  // Update fields
  await todoItem.getByRole('textbox').first().clear()
  await todoItem.getByRole('textbox').first().fill(newTitle)

  if (newDescription !== undefined) {
    const descField = todoItem.getByRole('textbox').nth(1)
    await descField.clear()
    if (newDescription) {
      await descField.fill(newDescription)
    }
  }

  if (newPriority) {
    await todoItem.getByRole('combobox').selectOption(newPriority)
  }

  await todoItem.getByRole('button', { name: /Save/i }).click()
}

export async function filterTodos(page: Page, filter: 'all' | 'active' | 'completed') {
  const filterButton = page.getByRole('button', { name: new RegExp(filter, 'i') })
  await filterButton.click()
  await page.waitForTimeout(200) // Wait for filter to apply
}

export async function getTodoCount(page: Page): Promise<number> {
  const todoItems = page.locator('[data-testid="todo-item"]')
  return await todoItems.count()
}

export async function waitForSSEConnection(page: Page) {
  // Wait for EventSource to be established
  await page.waitForFunction(() => {
    return window.__sseConnected === true
  }, { timeout: 10000 })
}

export async function mockGuestSession(page: Page, sessionId = 'guest-session-123') {
  await page.addInitScript((sessionId) => {
    localStorage.setItem('guest_session_id', sessionId)
  }, sessionId)
}

export async function clearAllTodos(page: Page) {
  const todoCount = await getTodoCount(page)

  if (todoCount > 0) {
    // Select all and delete
    await page.getByRole('button', { name: /Select All/i }).click()

    // Handle confirmation dialog
    page.once('dialog', dialog => dialog.accept())
    await page.getByRole('button', { name: /Delete Selected/i }).click()

    // Wait for todos to be cleared
    await page.waitForTimeout(500)
  }
}

export async function generateUniqueTitle(prefix: string): Promise<string> {
  return `${prefix} ${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
}

export async function waitForNetworkIdle(page: Page) {
  await page.waitForLoadState('networkidle')
}

// Mock API responses for testing error scenarios
export async function mockAPIError(page: Page, endpoint: string, statusCode: number) {
  await page.route(`**/api/${endpoint}`, route => {
    route.fulfill({
      status: statusCode,
      contentType: 'application/json',
      body: JSON.stringify({ error: 'Mocked error' })
    })
  })
}

export async function mockAPIDelay(page: Page, endpoint: string, delayMs: number) {
  await page.route(`**/api/${endpoint}`, async route => {
    await new Promise(resolve => setTimeout(resolve, delayMs))
    await route.continue()
  })
}

// Accessibility helpers
export async function checkA11y(page: Page) {
  // Basic accessibility checks
  const violations = await page.evaluate(() => {
    const issues = []

    // Check for missing alt text
    const images = document.querySelectorAll('img:not([alt])')
    if (images.length > 0) {
      issues.push(`${images.length} images missing alt text`)
    }

    // Check for missing labels
    const inputs = document.querySelectorAll('input:not([aria-label]):not([id])')
    if (inputs.length > 0) {
      issues.push(`${inputs.length} inputs missing labels`)
    }

    // Check for proper heading hierarchy
    const headings = Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, h6'))
    let lastLevel = 0
    headings.forEach(h => {
      const level = parseInt(h.tagName[1])
      if (level > lastLevel + 1) {
        issues.push(`Heading hierarchy issue: ${h.tagName} follows h${lastLevel}`)
      }
      lastLevel = level
    })

    return issues
  })

  return violations
}