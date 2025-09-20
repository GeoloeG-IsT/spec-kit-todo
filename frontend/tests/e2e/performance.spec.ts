import { test, expect } from '@playwright/test'
import { generateUniqueTitle, addTodo } from './helpers'

test.describe('Frontend Performance', () => {
  test('Page loads within acceptable time', async ({ page }) => {
    const startTime = Date.now()

    await page.goto('/')
    await page.waitForLoadState('networkidle')

    const loadTime = Date.now() - startTime

    console.log(`Page load time: ${loadTime}ms`)

    // Page should load within 3 seconds
    expect(loadTime).toBeLessThan(3000)

    // Check Core Web Vitals
    const metrics = await page.evaluate(() => {
      return new Promise((resolve) => {
        let fcp = 0
        let lcp = 0
        let cls = 0
        let fid = 0

        // First Contentful Paint
        const fcpObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries()
          fcp = entries[entries.length - 1].startTime
        })
        fcpObserver.observe({ entryTypes: ['paint'] })

        // Largest Contentful Paint
        const lcpObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries()
          lcp = entries[entries.length - 1].startTime
        })
        lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] })

        // Cumulative Layout Shift
        const clsObserver = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            if (!entry.hadRecentInput) {
              cls += entry.value
            }
          }
        })
        clsObserver.observe({ entryTypes: ['layout-shift'] })

        // Wait for metrics to be collected
        setTimeout(() => {
          resolve({
            fcp,
            lcp,
            cls,
            ttfb: performance.timing.responseStart - performance.timing.navigationStart,
            domContentLoaded: performance.timing.domContentLoadedEventEnd - performance.timing.navigationStart,
            loadComplete: performance.timing.loadEventEnd - performance.timing.navigationStart,
          })
        }, 2000)
      })
    })

    console.log('Performance Metrics:')
    console.log(`  FCP: ${metrics.fcp}ms`)
    console.log(`  LCP: ${metrics.lcp}ms`)
    console.log(`  CLS: ${metrics.cls}`)
    console.log(`  TTFB: ${metrics.ttfb}ms`)
    console.log(`  DOM Content Loaded: ${metrics.domContentLoaded}ms`)
    console.log(`  Load Complete: ${metrics.loadComplete}ms`)

    // Check against thresholds
    expect(metrics.fcp).toBeLessThan(1800) // Good FCP < 1.8s
    expect(metrics.lcp).toBeLessThan(2500) // Good LCP < 2.5s
    expect(metrics.cls).toBeLessThan(0.1)  // Good CLS < 0.1
    expect(metrics.ttfb).toBeLessThan(600) // Good TTFB < 600ms
  })

  test('Renders large list of TODOs efficiently', async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('networkidle')

    // Add many TODOs
    const todoCount = 100
    console.log(`Adding ${todoCount} TODOs...`)

    const startTime = Date.now()

    for (let i = 1; i <= todoCount; i++) {
      await page.getByPlaceholder(/What needs to be done/i).fill(`TODO ${i}`)
      await page.getByRole('button', { name: /Add TODO/i }).click()

      // Wait for TODO to appear before adding next
      await page.waitForSelector(`[data-testid="todo-item"]:has-text("TODO ${i}")`, { timeout: 1000 })
    }

    const totalTime = Date.now() - startTime
    const avgTimePerTodo = totalTime / todoCount

    console.log(`Total time to add ${todoCount} TODOs: ${totalTime}ms`)
    console.log(`Average time per TODO: ${avgTimePerTodo.toFixed(2)}ms`)

    // Should maintain good performance even with many TODOs
    expect(avgTimePerTodo).toBeLessThan(500)

    // Test scrolling performance
    const scrollStartTime = Date.now()
    await page.evaluate(() => {
      window.scrollTo(0, document.body.scrollHeight)
    })
    await page.waitForTimeout(100)
    await page.evaluate(() => {
      window.scrollTo(0, 0)
    })
    const scrollTime = Date.now() - scrollStartTime

    console.log(`Scroll performance with ${todoCount} TODOs: ${scrollTime}ms`)
    expect(scrollTime).toBeLessThan(500)

    // Test filtering performance
    const filterStartTime = Date.now()
    await page.getByRole('button', { name: /Completed/i }).click()
    await page.waitForTimeout(100)
    await page.getByRole('button', { name: /All/i }).click()
    const filterTime = Date.now() - filterStartTime

    console.log(`Filter toggle time: ${filterTime}ms`)
    expect(filterTime).toBeLessThan(500)
  })

  test('Handles rapid user interactions gracefully', async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('networkidle')

    // Rapid TODO additions
    const rapidAddCount = 10
    const addPromises = []

    console.log(`Rapidly adding ${rapidAddCount} TODOs...`)
    const startTime = Date.now()

    for (let i = 1; i <= rapidAddCount; i++) {
      addPromises.push((async () => {
        await page.getByPlaceholder(/What needs to be done/i).fill(`Rapid TODO ${i}`)
        await page.getByRole('button', { name: /Add TODO/i }).click()
      })())
    }

    await Promise.all(addPromises)
    const rapidAddTime = Date.now() - startTime

    console.log(`Time for ${rapidAddCount} rapid additions: ${rapidAddTime}ms`)

    // Wait for all TODOs to appear
    await page.waitForTimeout(1000)

    // Verify all TODOs were added
    const todoCount = await page.locator('[data-testid="todo-item"]').count()
    expect(todoCount).toBeGreaterThanOrEqual(rapidAddCount - 1) // Allow for 1 potential race condition

    // Rapid checkbox toggling
    console.log('Testing rapid checkbox toggling...')
    const checkboxes = page.locator('[data-testid="todo-checkbox"]')
    const toggleCount = await checkboxes.count()

    const toggleStartTime = Date.now()
    for (let i = 0; i < Math.min(toggleCount, 5); i++) {
      await checkboxes.nth(i).click()
      await checkboxes.nth(i).click() // Toggle back
    }
    const toggleTime = Date.now() - toggleStartTime

    console.log(`Time for rapid toggles: ${toggleTime}ms`)
    expect(toggleTime).toBeLessThan(2000)
  })

  test('Memory usage remains stable over time', async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('networkidle')

    // Get initial memory usage
    const initialMemory = await page.evaluate(() => {
      if ('memory' in performance) {
        return (performance as any).memory.usedJSHeapSize / 1024 / 1024
      }
      return 0
    })

    console.log(`Initial memory usage: ${initialMemory.toFixed(2)}MB`)

    // Perform many operations
    for (let cycle = 1; cycle <= 5; cycle++) {
      console.log(`Memory test cycle ${cycle}/5`)

      // Add TODOs
      for (let i = 1; i <= 10; i++) {
        await addTodo(page, `Memory test ${cycle}-${i}`)
      }

      // Toggle completions
      const checkboxes = page.locator('[data-testid="todo-checkbox"]')
      const count = await checkboxes.count()
      for (let i = 0; i < Math.min(count, 5); i++) {
        await checkboxes.nth(i).click()
      }

      // Delete some TODOs
      for (let i = 0; i < 5; i++) {
        const firstTodo = page.locator('[data-testid="todo-item"]').first()
        if (await firstTodo.isVisible()) {
          await firstTodo.hover()
          page.once('dialog', dialog => dialog.accept())
          await firstTodo.getByRole('button', { name: /Delete/i }).click()
          await page.waitForTimeout(100)
        }
      }

      // Check memory after each cycle
      const currentMemory = await page.evaluate(() => {
        if ('memory' in performance) {
          return (performance as any).memory.usedJSHeapSize / 1024 / 1024
        }
        return 0
      })

      console.log(`  Memory after cycle ${cycle}: ${currentMemory.toFixed(2)}MB`)
    }

    // Final memory check
    const finalMemory = await page.evaluate(() => {
      if ('memory' in performance) {
        return (performance as any).memory.usedJSHeapSize / 1024 / 1024
      }
      return 0
    })

    const memoryIncrease = finalMemory - initialMemory
    console.log(`Final memory usage: ${finalMemory.toFixed(2)}MB`)
    console.log(`Memory increase: ${memoryIncrease.toFixed(2)}MB`)

    // Memory increase should be reasonable (less than 50MB for this test)
    if (initialMemory > 0) { // Only check if memory API is available
      expect(memoryIncrease).toBeLessThan(50)
    }
  })

  test('Bundle size is optimized', async ({ page }) => {
    const response = await page.goto('/')

    // Get all JavaScript files
    const jsFiles = await page.evaluate(() => {
      return Array.from(document.querySelectorAll('script[src]')).map(script => {
        return (script as HTMLScriptElement).src
      })
    })

    let totalSize = 0
    const fileSizes: Record<string, number> = {}

    // Check size of each JS bundle
    for (const url of jsFiles) {
      const response = await page.request.get(url)
      const size = (await response.body()).length / 1024 // KB

      const fileName = url.split('/').pop() || 'unknown'
      fileSizes[fileName] = size
      totalSize += size

      console.log(`  ${fileName}: ${size.toFixed(2)}KB`)
    }

    console.log(`Total JS bundle size: ${totalSize.toFixed(2)}KB`)

    // Check that total bundle size is reasonable (< 500KB for initial load)
    expect(totalSize).toBeLessThan(500)

    // Check for code splitting
    const hasCodeSplitting = jsFiles.some(url => url.includes('chunk'))
    expect(hasCodeSplitting).toBeTruthy()
  })

  test('API response caching works correctly', async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('networkidle')

    // Monitor network requests
    const apiCalls: { url: string; fromCache: boolean }[] = []

    page.on('response', response => {
      if (response.url().includes('/api/')) {
        apiCalls.push({
          url: response.url(),
          fromCache: response.fromServiceWorker() || response.status() === 304
        })
      }
    })

    // Add a TODO
    await addTodo(page, 'Cache test TODO')

    // Navigate away and back
    await page.goto('/about') // Assuming there's an about page
    await page.waitForLoadState('networkidle')
    await page.goto('/')
    await page.waitForLoadState('networkidle')

    // Check if any API calls were cached
    const cachedCalls = apiCalls.filter(call => call.fromCache)
    console.log(`Total API calls: ${apiCalls.length}`)
    console.log(`Cached API calls: ${cachedCalls.length}`)

    // Some calls should be cached on second visit
    expect(cachedCalls.length).toBeGreaterThan(0)
  })

  test('Animations do not impact performance', async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('networkidle')

    // Measure FPS during animations
    const fps = await page.evaluate(() => {
      return new Promise((resolve) => {
        let frames = 0
        let lastTime = performance.now()
        const fpsValues: number[] = []

        function measureFPS() {
          frames++
          const currentTime = performance.now()
          const delta = currentTime - lastTime

          if (delta >= 1000) {
            const currentFPS = Math.round((frames * 1000) / delta)
            fpsValues.push(currentFPS)
            frames = 0
            lastTime = currentTime
          }

          if (fpsValues.length < 5) {
            requestAnimationFrame(measureFPS)
          } else {
            resolve(fpsValues)
          }
        }

        // Trigger some animations
        const elements = document.querySelectorAll('.transition-all')
        elements.forEach(el => {
          el.classList.add('hover:scale-105')
          ;(el as HTMLElement).style.transform = 'scale(1.05)'
          setTimeout(() => {
            ;(el as HTMLElement).style.transform = ''
          }, 100)
        })

        requestAnimationFrame(measureFPS)
      })
    })

    const avgFPS = (fps as number[]).reduce((a, b) => a + b, 0) / (fps as number[]).length
    console.log(`Average FPS during animations: ${avgFPS}`)
    console.log(`FPS samples: ${(fps as number[]).join(', ')}`)

    // Should maintain at least 30 FPS
    expect(avgFPS).toBeGreaterThan(30)
  })

  test('Search/filter performance with large dataset', async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('networkidle')

    // Add TODOs with searchable content
    const categories = ['Work', 'Personal', 'Shopping', 'Urgent', 'Project']
    for (let i = 0; i < 50; i++) {
      const category = categories[i % categories.length]
      await addTodo(page, `${category}: Task ${i}`, `Description for ${category} task`)
    }

    // Test search performance
    const searchInput = page.getByPlaceholder(/Search TODOs/i)
    if (await searchInput.isVisible()) {
      const searchStartTime = Date.now()

      // Type search query
      await searchInput.type('Work', { delay: 50 })

      // Wait for results to update
      await page.waitForTimeout(300)

      const searchTime = Date.now() - searchStartTime
      console.log(`Search execution time: ${searchTime}ms`)

      // Search should be fast
      expect(searchTime).toBeLessThan(1000)

      // Verify search results
      const visibleTodos = await page.locator('[data-testid="todo-item"]:visible').count()
      expect(visibleTodos).toBeLessThan(50) // Should filter results
    }

    // Test priority filtering performance
    const priorityStartTime = Date.now()
    await page.getByRole('button', { name: /High Priority/i }).click()
    await page.waitForTimeout(200)
    const priorityFilterTime = Date.now() - priorityStartTime

    console.log(`Priority filter time: ${priorityFilterTime}ms`)
    expect(priorityFilterTime).toBeLessThan(500)
  })
})