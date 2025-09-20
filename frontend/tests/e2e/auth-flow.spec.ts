import { test, expect } from '@playwright/test'

test.describe('Authenticated User Flow', () => {
  // Mock Clerk authentication for testing
  test.beforeEach(async ({ page }) => {
    // Set up mock authentication token
    await page.addInitScript(() => {
      // Mock Clerk's authentication state
      window.__clerk_session = {
        id: 'test-session-id',
        userId: 'test-user-id',
        status: 'active',
      }

      // Mock localStorage for Clerk
      localStorage.setItem('__clerk_client_jwt', 'mock-jwt-token')
      localStorage.setItem('__clerk_db_jwt', 'mock-db-jwt-token')
    })

    await page.goto('/')
    await page.waitForLoadState('networkidle')
  })

  test('Authenticated user sees personalized interface', async ({ page }) => {
    // Check for user-specific elements
    await expect(page.getByTestId('user-menu')).toBeVisible()
    await expect(page.getByText(/Sign up to save/i)).not.toBeVisible()

    // Check that TODO interface is available
    await expect(page.getByRole('heading', { name: /TODOs/i })).toBeVisible()
    await expect(page.getByPlaceholder(/What needs to be done/i)).toBeVisible()
  })

  test('Authenticated user TODOs are saved to their account', async ({ page }) => {
    const todoTitle = 'User TODO ' + Date.now()
    const todoDescription = 'This belongs to the user'

    // Add a TODO
    await page.getByPlaceholder(/What needs to be done/i).fill(todoTitle)
    await page.getByPlaceholder(/Add a description/i).fill(todoDescription)
    await page.getByRole('button', { name: /Add TODO/i }).click()

    // Verify TODO is created
    const todoItem = page.locator('[data-testid="todo-item"]').filter({ hasText: todoTitle })
    await expect(todoItem).toBeVisible()

    // TODO should have user association indicator
    await expect(todoItem).toHaveAttribute('data-owner', 'user')
  })

  test('Authenticated user can manage multiple TODOs efficiently', async ({ page }) => {
    // Add multiple TODOs
    const todos = [
      { title: 'First TODO', priority: 'high' },
      { title: 'Second TODO', priority: 'medium' },
      { title: 'Third TODO', priority: 'low' }
    ]

    for (const todo of todos) {
      await page.getByPlaceholder(/What needs to be done/i).fill(todo.title)
      await page.getByRole('combobox', { name: /Priority/i }).selectOption(todo.priority)
      await page.getByRole('button', { name: /Add TODO/i }).click()
      await page.waitForTimeout(100) // Small delay between additions
    }

    // Verify all TODOs are visible
    for (const todo of todos) {
      await expect(page.locator('[data-testid="todo-item"]').filter({ hasText: todo.title })).toBeVisible()
    }

    // Bulk operations - mark multiple as complete
    await page.getByRole('button', { name: /Select All/i }).click()
    await page.getByRole('button', { name: /Mark Selected Complete/i }).click()

    // Verify all are marked complete
    const todoItems = page.locator('[data-testid="todo-item"]')
    const count = await todoItems.count()
    for (let i = 0; i < count; i++) {
      await expect(todoItems.nth(i)).toHaveClass(/completed/)
    }
  })
})

test.describe('Guest to User Conversion Flow', () => {
  test('Guest user can convert session after sign-up', async ({ page, context }) => {
    // Start as guest and add TODOs
    await page.goto('/')
    await page.waitForLoadState('networkidle')

    const guestTodo1 = 'Guest TODO 1 ' + Date.now()
    const guestTodo2 = 'Guest TODO 2 ' + Date.now()

    // Add guest TODOs
    await page.getByPlaceholder(/What needs to be done/i).fill(guestTodo1)
    await page.getByRole('button', { name: /Add TODO/i }).click()

    await page.getByPlaceholder(/What needs to be done/i).fill(guestTodo2)
    await page.getByRole('button', { name: /Add TODO/i }).click()

    // Mark one as complete
    await page.locator('[data-testid="todo-item"]')
      .filter({ hasText: guestTodo1 })
      .locator('[data-testid="todo-checkbox"]')
      .click()

    // Get session ID from cookies/storage
    const sessionId = await page.evaluate(() => {
      return localStorage.getItem('guest_session_id')
    })

    // Click sign-up
    await page.getByRole('button', { name: /Sign Up/i }).click()

    // Mock successful sign-up and return
    await page.addInitScript((sessionId) => {
      window.__clerk_session = {
        id: 'new-user-session',
        userId: 'new-user-id',
        status: 'active',
      }

      // Preserve guest session for conversion
      localStorage.setItem('pending_conversion_session', sessionId)
      localStorage.setItem('__clerk_client_jwt', 'new-user-jwt-token')
    }, sessionId)

    // Navigate back after "sign-up"
    await page.goto('/')
    await page.waitForLoadState('networkidle')

    // Check for conversion prompt
    await expect(page.getByText(/Import your guest TODOs/i)).toBeVisible()
    await page.getByRole('button', { name: /Import TODOs/i }).click()

    // Wait for conversion to complete
    await page.waitForResponse(resp => resp.url().includes('/api/auth/session/convert'))

    // Verify TODOs are still present
    await expect(page.locator('[data-testid="todo-item"]').filter({ hasText: guestTodo1 })).toBeVisible()
    await expect(page.locator('[data-testid="todo-item"]').filter({ hasText: guestTodo2 })).toBeVisible()

    // Verify completion status is preserved
    await expect(page.locator('[data-testid="todo-item"]').filter({ hasText: guestTodo1 })).toHaveClass(/completed/)
    await expect(page.locator('[data-testid="todo-item"]').filter({ hasText: guestTodo2 })).not.toHaveClass(/completed/)

    // Verify TODOs now belong to user
    const todoItems = page.locator('[data-testid="todo-item"]')
    const count = await todoItems.count()
    for (let i = 0; i < count; i++) {
      await expect(todoItems.nth(i)).toHaveAttribute('data-owner', 'user')
    }
  })

  test('User can choose to skip importing guest TODOs', async ({ page }) => {
    // Add guest TODOs
    await page.goto('/')
    const guestTodo = 'Guest TODO to skip ' + Date.now()
    await page.getByPlaceholder(/What needs to be done/i).fill(guestTodo)
    await page.getByRole('button', { name: /Add TODO/i }).click()

    // Mock sign-in with existing user
    await page.addInitScript(() => {
      window.__clerk_session = {
        id: 'existing-user-session',
        userId: 'existing-user-id',
        status: 'active',
      }
      localStorage.setItem('pending_conversion_session', 'guest-session-id')
      localStorage.setItem('__clerk_client_jwt', 'existing-user-jwt-token')
    })

    await page.goto('/')
    await page.waitForLoadState('networkidle')

    // Check for conversion prompt
    await expect(page.getByText(/Import your guest TODOs/i)).toBeVisible()

    // Click skip
    await page.getByRole('button', { name: /Skip|Don't Import/i }).click()

    // Guest TODOs should not be visible
    await expect(page.locator('[data-testid="todo-item"]').filter({ hasText: guestTodo })).not.toBeVisible()

    // Conversion prompt should be dismissed
    await expect(page.getByText(/Import your guest TODOs/i)).not.toBeVisible()
  })
})

test.describe('Real-time Sync', () => {
  test('Multiple tabs sync in real-time via SSE', async ({ browser }) => {
    // Open two tabs
    const context1 = await browser.newContext()
    const page1 = await context1.newPage()

    const context2 = await browser.newContext()
    const page2 = await context2.newPage()

    // Set up same user session for both
    const setupAuth = async (page: any) => {
      await page.addInitScript(() => {
        window.__clerk_session = {
          id: 'shared-session',
          userId: 'shared-user-id',
          status: 'active',
        }
        localStorage.setItem('__clerk_client_jwt', 'shared-jwt-token')
      })
    }

    await setupAuth(page1)
    await setupAuth(page2)

    // Navigate both pages
    await page1.goto('/')
    await page2.goto('/')

    await page1.waitForLoadState('networkidle')
    await page2.waitForLoadState('networkidle')

    // Add TODO in page1
    const todoTitle = 'Real-time sync TODO ' + Date.now()
    await page1.getByPlaceholder(/What needs to be done/i).fill(todoTitle)
    await page1.getByRole('button', { name: /Add TODO/i }).click()

    // Verify it appears in page1
    await expect(page1.locator('[data-testid="todo-item"]').filter({ hasText: todoTitle })).toBeVisible()

    // Wait for SSE sync and verify it appears in page2
    await expect(page2.locator('[data-testid="todo-item"]').filter({ hasText: todoTitle })).toBeVisible({ timeout: 5000 })

    // Update TODO in page2
    const todoItem2 = page2.locator('[data-testid="todo-item"]').filter({ hasText: todoTitle })
    await todoItem2.locator('[data-testid="todo-checkbox"]').click()

    // Verify update syncs to page1
    const todoItem1 = page1.locator('[data-testid="todo-item"]').filter({ hasText: todoTitle })
    await expect(todoItem1).toHaveClass(/completed/, { timeout: 5000 })

    // Clean up
    await context1.close()
    await context2.close()
  })
})

test.describe('Performance and Edge Cases', () => {
  test('Handles network errors gracefully', async ({ page, context }) => {
    await page.goto('/')

    // Add a TODO
    const todoTitle = 'Offline TODO ' + Date.now()
    await page.getByPlaceholder(/What needs to be done/i).fill(todoTitle)

    // Go offline
    await context.setOffline(true)

    // Try to add TODO
    await page.getByRole('button', { name: /Add TODO/i }).click()

    // Should show error message
    await expect(page.getByText(/Unable to save|Connection error/i)).toBeVisible({ timeout: 5000 })

    // Go back online
    await context.setOffline(false)

    // Retry should work
    await page.getByRole('button', { name: /Retry|Try Again/i }).click()

    // TODO should be saved
    await expect(page.locator('[data-testid="todo-item"]').filter({ hasText: todoTitle })).toBeVisible()
  })

  test('Handles large number of TODOs efficiently', async ({ page }) => {
    await page.goto('/')

    // Add multiple TODOs quickly
    const startTime = Date.now()
    const todoCount = 20

    for (let i = 1; i <= todoCount; i++) {
      await page.getByPlaceholder(/What needs to be done/i).fill(`TODO ${i}`)
      await page.getByRole('button', { name: /Add TODO/i }).click()
      // Don't wait between additions to test performance
    }

    const endTime = Date.now()
    const totalTime = endTime - startTime

    // Should complete in reasonable time (less than 10 seconds for 20 TODOs)
    expect(totalTime).toBeLessThan(10000)

    // All TODOs should be visible
    const todoItems = page.locator('[data-testid="todo-item"]')
    await expect(todoItems).toHaveCount(todoCount)

    // Page should remain responsive
    await page.getByRole('button', { name: /Active/i }).click()
    await page.getByRole('button', { name: /All/i }).click()

    // Should handle bulk operations
    await page.getByRole('button', { name: /Select All/i }).click()
    await page.getByRole('button', { name: /Delete Selected/i }).click()

    // Handle confirmation
    page.on('dialog', dialog => dialog.accept())

    // All TODOs should be deleted
    await expect(todoItems).toHaveCount(0, { timeout: 5000 })
  })
})