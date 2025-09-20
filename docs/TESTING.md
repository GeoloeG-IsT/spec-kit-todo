# Testing Guide

## Overview

The TODO application has comprehensive test coverage including:
- Unit tests for all services and components
- Integration tests for API endpoints
- End-to-end tests for user workflows
- Performance and load testing
- Accessibility testing

## Running Tests

### Backend Tests

#### Unit Tests
```bash
cd backend

# Run all unit tests
pytest tests/unit/

# Run specific test file
pytest tests/unit/test_todo_service.py

# Run with coverage
pytest tests/unit/ --cov=src --cov-report=html

# Run with verbose output
pytest tests/unit/ -v
```

#### Integration Tests
```bash
# Start test database
docker-compose up -d postgres-test

# Run integration tests
pytest tests/integration/

# Run specific integration test
pytest tests/integration/test_todo_api.py::test_create_todo
```

#### Contract Tests
```bash
# Run contract tests
pytest tests/contract/

# Run specific contract test suite
pytest tests/contract/test_todos_create.py
```

#### Performance Tests
```bash
# Start the API server
uvicorn src.main:app --port 8000

# In another terminal, run performance tests
pytest tests/performance/ -v

# Run load tests only
pytest tests/performance/test_api_performance.py::TestLoadScenarios
```

#### All Backend Tests
```bash
# Run all tests with coverage report
pytest --cov=src --cov-report=html --cov-report=term-missing

# Generate coverage badge
coverage-badge -o coverage.svg
```

### Frontend Tests

#### Unit Tests
```bash
cd frontend

# Run unit tests
npm test

# Run tests in watch mode
npm run test:watch

# Run with coverage
npm test -- --coverage

# Run specific test file
npm test Button.test
```

#### E2E Tests
```bash
# Install Playwright browsers (first time only)
npx playwright install

# Run all E2E tests
npm run test:e2e

# Run E2E tests in headed mode (see browser)
npx playwright test --headed

# Run specific test file
npx playwright test guest-flow.spec.ts

# Run tests in specific browser
npx playwright test --project=chromium

# Run tests with debugging
npx playwright test --debug

# Open Playwright UI mode
npx playwright test --ui
```

#### Performance Tests
```bash
# Run performance tests
npx playwright test performance.spec.ts

# Run with performance profiling
npx playwright test performance.spec.ts --trace on
```

#### Accessibility Tests
```bash
# Run accessibility tests
npx playwright test accessibility.spec.ts

# Run on different devices
npx playwright test accessibility.spec.ts --device="iPhone 12"
```

## Test Coverage Goals

### Backend Coverage (Target: 80%+)
- ✅ Services: 90%+
- ✅ API Routes: 85%+
- ✅ Models: 80%+
- ✅ Middleware: 85%+

### Frontend Coverage (Target: 70%+)
- ✅ Components: 80%+
- ✅ Hooks: 75%+
- ✅ Utils: 90%+
- ✅ API Client: 85%+

## Test Organization

```
backend/tests/
├── unit/               # Fast, isolated unit tests
│   ├── test_auth_service.py
│   ├── test_todo_service.py
│   └── test_user_service.py
├── integration/        # API integration tests
│   ├── test_todo_api.py
│   └── test_auth_flow.py
├── contract/          # Contract tests against API spec
│   ├── test_todos_create.py
│   ├── test_todos_update.py
│   └── test_auth_session.py
└── performance/       # Performance and load tests
    └── test_api_performance.py

frontend/tests/
├── unit/              # Component unit tests
│   ├── Button.test.tsx
│   └── TodoItem.test.tsx
└── e2e/               # End-to-end tests
    ├── guest-flow.spec.ts
    ├── auth-flow.spec.ts
    ├── accessibility.spec.ts
    ├── performance.spec.ts
    └── helpers.ts
```

## Continuous Integration

Tests run automatically on:
- Pull request creation/update
- Push to main branch
- Scheduled daily runs

### GitHub Actions Workflow

```yaml
name: Test Suite

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: |
          pip install -r backend/requirements.txt
          pytest backend/tests/ --cov=backend/src

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '18'
      - run: |
          cd frontend
          npm ci
          npm test
          npx playwright install
          npx playwright test
```

## Testing Best Practices

### Unit Tests
- Test one thing at a time
- Use descriptive test names
- Mock external dependencies
- Keep tests fast (< 100ms each)
- Follow AAA pattern (Arrange, Act, Assert)

### Integration Tests
- Test complete workflows
- Use test database
- Clean up after tests
- Test error scenarios
- Verify response schemas

### E2E Tests
- Test critical user paths
- Use page object pattern
- Handle async operations properly
- Test on multiple viewports
- Include accessibility checks

### Performance Tests
- Set clear performance budgets
- Test under realistic load
- Monitor memory usage
- Test with production-like data
- Include stress testing

## Debugging Tests

### Backend Debugging
```bash
# Run with pytest debugger
pytest tests/unit/test_todo_service.py::test_create_todo --pdb

# Run with logging
pytest tests/unit/ --log-cli-level=DEBUG

# Run specific test with print statements
pytest tests/unit/test_auth_service.py::test_create_session -s
```

### Frontend Debugging
```bash
# Debug in VS Code
# Add breakpoint in test file and run:
npm test -- --runInBand

# Debug E2E tests
npx playwright test --debug

# View test trace
npx playwright show-trace trace.zip

# Generate screenshots on failure
npx playwright test --screenshot=only-on-failure
```

## Test Data Management

### Backend Test Data
```python
# Use fixtures for test data
@pytest.fixture
def sample_todo():
    return {
        "title": "Test TODO",
        "description": "Test description",
        "priority": "medium"
    }

# Use factories for complex data
class TodoFactory:
    @staticmethod
    def create_todo(**kwargs):
        defaults = {
            "title": f"TODO {uuid4()}",
            "priority": "medium"
        }
        return {**defaults, **kwargs}
```

### Frontend Test Data
```typescript
// Use test data builders
const createMockTodo = (overrides = {}): TodoItemResponse => ({
  id: 'test-id',
  title: 'Test TODO',
  completed: false,
  priority: 'medium',
  order_index: 0,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  ...overrides
})

// Use MSW for API mocking
import { setupServer } from 'msw/node'
import { rest } from 'msw'

const server = setupServer(
  rest.get('/api/todos', (req, res, ctx) => {
    return res(ctx.json({ items: [createMockTodo()] }))
  })
)
```

## Monitoring Test Health

### Track Metrics
- Test execution time
- Test flakiness rate
- Coverage trends
- Failed test patterns

### Fix Flaky Tests
1. Identify flaky tests from CI logs
2. Add proper waits/retries
3. Fix race conditions
4. Improve test isolation
5. Use deterministic test data

### Regular Maintenance
- Update test dependencies monthly
- Review and refactor slow tests
- Remove redundant tests
- Update tests for new features
- Maintain test documentation

## Troubleshooting Common Issues

### Backend Test Issues

**ImportError: No module named 'src'**
```bash
# Run from backend directory
cd backend
export PYTHONPATH=$PYTHONPATH:$(pwd)
pytest tests/
```

**Database connection errors**
```bash
# Ensure test database is running
docker-compose up -d postgres-test

# Check DATABASE_TEST_URL
export DATABASE_TEST_URL=postgresql://test:test@localhost:5433/test_db
```

**Async test failures**
```python
# Use pytest-asyncio
@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result is not None
```

### Frontend Test Issues

**Jest configuration errors**
```bash
# Clear Jest cache
npm test -- --clearCache

# Update Jest config
npm test -- --updateSnapshot
```

**Playwright timeout errors**
```typescript
// Increase timeout for slow operations
test('slow test', async ({ page }) => {
  test.setTimeout(60000); // 60 seconds
  await page.goto('/');
});
```

**React Testing Library queries**
```typescript
// Use correct query method
const button = screen.getByRole('button', { name: /submit/i });
// Not: screen.getByText('Submit')
```

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [Jest Documentation](https://jestjs.io/docs/getting-started)
- [Playwright Documentation](https://playwright.dev/docs/intro)
- [React Testing Library](https://testing-library.com/docs/react-testing-library/intro/)
- [Testing Best Practices](https://github.com/goldbergyoni/javascript-testing-best-practices)