# Spec Kit Todo Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-01-19

## Active Technologies
- **Backend**: Python 3.11, FastAPI, SQLModel, httpx, Pydantic
- **Frontend**: TypeScript, Next.js 14+, React 18+, TailwindCSS, TanStack Query
- **Database**: PostgreSQL with Neon (serverless, branching)
- **Authentication**: Clerk (email/password + OAuth: Google, GitHub, LinkedIn)
- **Testing**: pytest, pytest-asyncio (backend), Jest, React Testing Library, Playwright (frontend)
- **Deployment**: GCP Cloud Run, GitHub Actions CI/CD, Artifact Registry
- **Real-time**: Server-Sent Events (SSE) for sync
- **Infrastructure**: Docker, Google Secret Manager

## Project Structure
```
backend/
├── src/
│   ├── domain/          # Domain entities and value objects
│   │   ├── models/      # SQLModel entities
│   │   └── schemas/     # Pydantic schemas
│   ├── services/        # Business logic layer
│   ├── api/             # FastAPI routes and dependencies
│   │   ├── routes/
│   │   └── middleware/
│   ├── infrastructure/  # External services (DB, Auth, etc.)
│   └── cli/             # CLI commands
├── tests/
│   ├── contract/
│   ├── integration/
│   └── unit/
└── requirements.txt

frontend/
├── src/
│   ├── app/             # Next.js app directory
│   │   ├── (auth)/      # Auth-protected routes
│   │   └── api/         # API routes (if needed)
│   ├── components/      # React components
│   │   ├── ui/          # Base UI components
│   │   └── features/    # Feature-specific components
│   ├── lib/             # Utilities and helpers
│   │   ├── api/         # API client with TanStack Query
│   │   └── auth/        # Clerk integration
│   └── styles/          # Global styles and Tailwind config
├── tests/
│   ├── e2e/             # Playwright tests
│   └── unit/            # Component tests
├── package.json
└── tsconfig.json

# Infrastructure
.github/workflows/       # GitHub Actions CI/CD
docker/                  # Dockerfiles
docker-compose.yml       # Local development
```

## Commands

### Backend Development
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8000
```

### Frontend Development
```bash
cd frontend
npm install
npm run dev              # Development server
npm run build            # Production build
npm run test             # Run tests
npm run test:e2e         # Run Playwright tests
```

### Database (Neon)
```bash
# Create development branch
neon branches create --name dev/local
export DATABASE_URL=$(neon connection-string dev/local)

# Run migrations
alembic upgrade head
```

### Testing
```bash
# Backend tests
cd backend
pytest                   # All tests
pytest tests/unit/       # Unit tests only
pytest tests/integration/  # Integration tests

# Frontend tests
cd frontend
npm run test             # Unit tests
npm run test:e2e         # E2E tests with Playwright
```

### Docker Development
```bash
docker-compose up        # Start all services
docker-compose up -d     # Start in background
docker-compose down      # Stop services
docker-compose logs backend  # View backend logs
```

## Code Style

### Python (Backend)
- Follow PEP 8 with Black formatting
- Use type hints everywhere
- SQLModel for database models
- Pydantic for API schemas
- Async/await for all I/O operations
- Dependency injection pattern

Example:
```python
from fastapi import FastAPI, Depends
from sqlmodel import SQLModel, Session
from typing import List

async def get_todos(
    user_id: UUID = Depends(get_current_user),
    session: Session = Depends(get_db_session)
) -> List[TodoItemResponse]:
    return await todo_service.get_user_todos(user_id, session)
```

### TypeScript (Frontend)
- Strict TypeScript configuration
- React functional components with hooks
- TanStack Query for server state
- Tailwind for styling
- Component composition over inheritance

Example:
```typescript
interface TodoItemProps {
  todo: TodoItem;
  onUpdate: (todo: TodoItem) => void;
}

export function TodoItem({ todo, onUpdate }: TodoItemProps) {
  const { mutate: updateTodo } = useUpdateTodo();

  return (
    <div className="flex items-center space-x-2 p-3 bg-gray-900 border border-cyan-500">
      {/* Component content */}
    </div>
  );
}
```

### Cyberpunk Theme
- **Colors**: Neon cyan (#00FFFF), magenta (#FF00FF), electric purple (#8A2BE2)
- **Fonts**: Monospace (JetBrains Mono, Fira Code, or system monospace)
- **Effects**: Subtle scanlines, glitch hover effects, holographic borders
- **Background**: Dark theme with gradients

## Recent Changes
- **001-a-todo-list**: Added full-stack TODO app with FastAPI backend, Next.js frontend, Clerk auth, Neon PostgreSQL, and real-time sync via SSE

## Constitutional Principles
- **Clean Architecture**: Domain logic separated from infrastructure
- **Test-First Development**: TDD with contract tests before implementation
- **Library-First**: Modular, reusable components
- **SOLID Principles**: Single responsibility, dependency injection
- **DRY**: Shared schemas via OpenAPI, no code duplication
- **KISS**: Use established patterns and frameworks
- **YAGNI**: Only implement specified features

## Environment Variables

### Backend (.env)
```bash
DATABASE_URL=postgresql://user:pass@ep-xxx.region.aws.neon.tech/dbname
CLERK_SECRET_KEY=sk_test_...
CLERK_PUBLISHABLE_KEY=pk_test_...
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
LOG_LEVEL=INFO
```

### Frontend (.env.local)
```bash
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in
NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Production
- Use Google Secret Manager for sensitive values
- Configure Workload Identity Federation for GitHub Actions
- Set up custom domain with SSL certificate

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->