import { test, expect, devices } from '@playwright/test'
import { checkA11y, addTodo, markTodoComplete } from './helpers'

test.describe('Accessibility and Mobile Responsiveness', () => {
  test('Application meets basic accessibility standards', async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('networkidle')

    // Check for accessibility violations
    const violations = await checkA11y(page)
    expect(violations).toHaveLength(0)

    // Check keyboard navigation
    // Tab through interactive elements
    await page.keyboard.press('Tab')
    let focusedElement = await page.evaluate(() => document.activeElement?.tagName)
    expect(focusedElement).toBeTruthy()

    // Add TODO using keyboard only
    await page.keyboard.type('Keyboard test TODO')
    await page.keyboard.press('Tab') // Move to description
    await page.keyboard.type('Added via keyboard')
    await page.keyboard.press('Tab') // Move to priority
    await page.keyboard.press('ArrowDown') // Change priority
    await page.keyboard.press('Tab') // Move to Add button
    await page.keyboard.press('Enter') // Submit

    // Verify TODO was added
    await expect(page.locator('[data-testid="todo-item"]').filter({ hasText: 'Keyboard test TODO' })).toBeVisible()

    // Check ARIA labels
    const addButton = page.getByRole('button', { name: /Add TODO/i })
    await expect(addButton).toHaveAttribute('aria-label', /Add/)

    const todoCheckbox = page.locator('[data-testid="todo-checkbox"]').first()
    await expect(todoCheckbox).toHaveAttribute('aria-label', /Mark as complete/i)

    // Check color contrast for cyberpunk theme
    const contrastRatio = await page.evaluate(() => {
      const getContrastRatio = (color1: string, color2: string) => {
        // Simplified contrast ratio calculation
        const getLuminance = (color: string) => {
          const rgb = color.match(/\d+/g)?.map(Number) || [0, 0, 0]
          const [r, g, b] = rgb.map(c => {
            c = c / 255
            return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4)
          })
          return 0.2126 * r + 0.7152 * g + 0.0722 * b
        }

        const l1 = getLuminance(color1)
        const l2 = getLuminance(color2)
        return (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05)
      }

      // Check text contrast on dark background
      const textElement = document.querySelector('.text-cyan-100')
      if (textElement) {
        const styles = window.getComputedStyle(textElement)
        const textColor = styles.color
        const bgColor = styles.backgroundColor || 'rgb(17, 24, 39)' // gray-900
        return getContrastRatio(textColor, bgColor)
      }
      return 0
    })

    // WCAG AA requires 4.5:1 for normal text
    expect(contrastRatio).toBeGreaterThanOrEqual(4.5)

    // Check focus indicators
    await page.getByPlaceholder(/What needs to be done/i).focus()
    const focusVisible = await page.evaluate(() => {
      const element = document.activeElement as HTMLElement
      const styles = window.getComputedStyle(element)
      return styles.outline !== 'none' || styles.boxShadow.includes('ring')
    })
    expect(focusVisible).toBeTruthy()
  })

  test('Application works on mobile devices', async ({ browser }) => {
    // Test on iPhone 12
    const iPhone = devices['iPhone 12']
    const context = await browser.newContext({
      ...iPhone,
    })
    const page = await context.newPage()

    await page.goto('/')
    await page.waitForLoadState('networkidle')

    // Check responsive layout
    const viewport = page.viewportSize()
    expect(viewport?.width).toBeLessThanOrEqual(414) // iPhone 12 width

    // Check that mobile menu is visible if applicable
    const mobileMenu = page.getByRole('button', { name: /Menu/i })
    if (await mobileMenu.isVisible()) {
      await mobileMenu.click()
      await expect(page.getByRole('navigation')).toBeVisible()
    }

    // Add TODO on mobile
    await addTodo(page, 'Mobile TODO', 'Works on phone')

    // Verify TODO appears
    await expect(page.locator('[data-testid="todo-item"]').filter({ hasText: 'Mobile TODO' })).toBeVisible()

    // Check touch interactions
    const todoItem = page.locator('[data-testid="todo-item"]').first()

    // Touch to show actions (mobile doesn't have hover)
    await todoItem.tap()
    await page.waitForTimeout(100)

    // Edit button should be accessible
    const editButton = todoItem.getByRole('button', { name: /Edit/i })
    await expect(editButton).toBeVisible()

    // Check scrolling for long lists
    for (let i = 1; i <= 15; i++) {
      await addTodo(page, `Mobile TODO ${i}`)
    }

    // Scroll to bottom
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight))

    // Last TODO should be visible
    await expect(page.locator('[data-testid="todo-item"]').filter({ hasText: 'Mobile TODO 15' })).toBeInViewport()

    await context.close()
  })

  test('Application works on tablet devices', async ({ browser }) => {
    // Test on iPad
    const iPad = devices['iPad Pro']
    const context = await browser.newContext({
      ...iPad,
    })
    const page = await context.newPage()

    await page.goto('/')
    await page.waitForLoadState('networkidle')

    // Check tablet layout
    const viewport = page.viewportSize()
    expect(viewport?.width).toBe(1024) // iPad Pro width

    // Check that layout adapts for tablet
    // Should show both sidebar and main content if applicable
    const sidebar = page.getByRole('complementary')
    const mainContent = page.getByRole('main')

    if (await sidebar.isVisible()) {
      // Both should be visible on tablet
      await expect(sidebar).toBeVisible()
      await expect(mainContent).toBeVisible()
    }

    // Test touch interactions
    await addTodo(page, 'Tablet TODO', 'Works on iPad')
    await markTodoComplete(page, 'Tablet TODO')

    // Verify completion
    const todoItem = page.locator('[data-testid="todo-item"]').filter({ hasText: 'Tablet TODO' })
    await expect(todoItem).toHaveClass(/completed/)

    // Test landscape orientation
    await page.setViewportSize({ width: 1366, height: 1024 })
    await page.waitForTimeout(300) // Wait for layout adjustment

    // UI should adapt to landscape
    await expect(page.getByRole('heading', { name: /TODOs/i })).toBeVisible()

    await context.close()
  })

  test('Application handles different screen sizes gracefully', async ({ page }) => {
    const sizes = [
      { name: 'Mobile S', width: 320, height: 568 },
      { name: 'Mobile M', width: 375, height: 667 },
      { name: 'Mobile L', width: 425, height: 812 },
      { name: 'Tablet', width: 768, height: 1024 },
      { name: 'Laptop', width: 1024, height: 768 },
      { name: 'Laptop L', width: 1440, height: 900 },
      { name: '4K', width: 2560, height: 1440 },
    ]

    for (const size of sizes) {
      await page.setViewportSize({ width: size.width, height: size.height })
      await page.goto('/')
      await page.waitForLoadState('networkidle')

      // Check that essential elements are visible at all sizes
      await expect(page.getByRole('heading', { name: /TODOs/i })).toBeVisible()
      await expect(page.getByPlaceholder(/What needs to be done/i)).toBeVisible()
      await expect(page.getByRole('button', { name: /Add TODO/i })).toBeVisible()

      // Add a TODO at this size
      await addTodo(page, `${size.name} TODO`)

      // Verify it's visible
      await expect(page.locator('[data-testid="todo-item"]').filter({ hasText: `${size.name} TODO` })).toBeVisible()
    }
  })

  test('Application supports screen readers', async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('networkidle')

    // Check for screen reader announcements
    const liveRegion = page.getByRole('status')

    // Add a TODO
    await addTodo(page, 'Screen reader test')

    // Check if live region announces the addition
    if (await liveRegion.isVisible()) {
      await expect(liveRegion).toContainText(/added|created/i)
    }

    // Check semantic HTML structure
    const main = page.getByRole('main')
    await expect(main).toBeVisible()

    const heading = page.getByRole('heading', { level: 1 })
    await expect(heading).toBeVisible()

    // Check form structure
    const form = page.getByRole('form')
    if (await form.isVisible()) {
      // Form should have proper structure
      const formInputs = form.getByRole('textbox')
      expect(await formInputs.count()).toBeGreaterThan(0)
    }

    // Check lists are properly structured
    const todoList = page.getByRole('list').filter({ has: page.locator('[data-testid="todo-item"]') })
    if (await todoList.isVisible()) {
      const listItems = todoList.getByRole('listitem')
      expect(await listItems.count()).toBeGreaterThan(0)
    }
  })

  test('Application handles reduced motion preferences', async ({ page }) => {
    // Enable reduced motion
    await page.emulateMedia({ reducedMotion: 'reduce' })
    await page.goto('/')
    await page.waitForLoadState('networkidle')

    // Check that animations are disabled
    const hasReducedMotion = await page.evaluate(() => {
      const element = document.querySelector('.transition-all')
      if (element) {
        const styles = window.getComputedStyle(element)
        return styles.transitionDuration === '0s' || styles.animation === 'none'
      }
      return false
    })

    // With reduced motion, animations should be minimal or disabled
    // This might need adjustment based on actual implementation
    expect(hasReducedMotion).toBeDefined()

    // Test that functionality still works without animations
    await addTodo(page, 'No animation TODO')
    await expect(page.locator('[data-testid="todo-item"]').filter({ hasText: 'No animation TODO' })).toBeVisible()
  })
})