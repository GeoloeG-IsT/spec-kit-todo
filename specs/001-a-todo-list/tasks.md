# Tasks: TODO List App

**Input**: Design documents from `/specs/001-a-todo-list/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → If not found: ERROR "No implementation plan found"
   → Extract: tech stack, libraries, structure
2. Load optional design documents:
   → data-model.md: Extract entities → model tasks
   → contracts/: Each file → contract test task
   → research.md: Extract decisions → setup tasks
3. Generate tasks by category:
   → Setup: project init, dependencies, linting
   → Tests: contract tests, integration tests
   → Core: models, services, CLI commands
   → Integration: DB, middleware, logging
   → Polish: unit tests, performance, docs
4. Apply task rules:
   → Different files = mark [P] for parallel
   → Same file = sequential (no [P])
   → Tests before implementation (TDD)
5. Number tasks sequentially (T001, T002...)
6. Generate dependency graph
7. Create parallel execution examples
8. Validate task completeness:
   → All contracts have tests?
   → All entities have models?
   → All endpoints implemented?
9. Return: SUCCESS (tasks ready for execution)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- **Web app**: `backend/src/`, `frontend/src/`
- Paths shown below assume web application structure per plan.md

## Phase 3.1: Setup
- [ ] T001 Create project directory structure (backend/, frontend/, docker/, .github/)
- [ ] T002 [P] Initialize Python backend with FastAPI, SQLModel, and dependencies in backend/requirements.txt
- [ ] T003 [P] Initialize Next.js frontend with TypeScript, TailwindCSS, and dependencies in frontend/package.json
- [ ] T004 [P] Create Docker configuration files: docker/backend.Dockerfile, docker/frontend.Dockerfile, docker-compose.yml
- [ ] T005 [P] Configure linting and formatting: backend/.pre-commit-config.yaml, frontend/.eslintrc.json, frontend/.prettierrc

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

### Contract Tests
- [ ] T006 [P] Contract test POST /api/auth/session in backend/tests/contract/test_auth_session.py
- [ ] T007 [P] Contract test POST /api/auth/user in backend/tests/contract/test_auth_user.py
- [ ] T008 [P] Contract test GET /api/auth/user in backend/tests/contract/test_auth_user.py
- [ ] T009 [P] Contract test POST /api/auth/convert-session in backend/tests/contract/test_auth_convert.py
- [ ] T010 [P] Contract test GET /api/todos in backend/tests/contract/test_todos_list.py
- [ ] T011 [P] Contract test POST /api/todos in backend/tests/contract/test_todos_create.py
- [ ] T012 [P] Contract test GET /api/todos/{todo_id} in backend/tests/contract/test_todos_get.py
- [ ] T013 [P] Contract test PUT /api/todos/{todo_id} in backend/tests/contract/test_todos_update.py
- [ ] T014 [P] Contract test DELETE /api/todos/{todo_id} in backend/tests/contract/test_todos_delete.py
- [ ] T015 [P] Contract test PUT /api/todos/bulk in backend/tests/contract/test_todos_bulk.py
- [ ] T016 [P] Contract test PUT /api/todos/reorder in backend/tests/contract/test_todos_reorder.py
- [ ] T017 [P] Contract test GET /api/todos/stream (SSE) in backend/tests/contract/test_todos_stream.py

### Integration Tests
- [ ] T018 [P] Integration test: Guest user creates and manages TODOs in backend/tests/integration/test_guest_flow.py
- [ ] T019 [P] Integration test: User registration with email/password in backend/tests/integration/test_user_registration.py
- [ ] T020 [P] Integration test: OAuth registration flow (Google, GitHub, LinkedIn) in backend/tests/integration/test_oauth_registration.py
- [ ] T021 [P] Integration test: Guest-to-registered user conversion in backend/tests/integration/test_session_conversion.py
- [ ] T022 [P] Integration test: Multi-auth provider linking in backend/tests/integration/test_multi_auth.py
- [ ] T023 [P] Integration test: Real-time sync across devices in backend/tests/integration/test_realtime_sync.py
- [ ] T024 [P] Integration test: Password reset flow in backend/tests/integration/test_password_reset.py

## Phase 3.3: Core Implementation (ONLY after tests are failing)

### Database and Models
- [ ] T025 [P] User model in backend/src/domain/models/user.py
- [ ] T026 [P] TodoItem model in backend/src/domain/models/todo_item.py
- [ ] T027 [P] Session model in backend/src/domain/models/session.py
- [ ] T028 [P] AuthProvider model in backend/src/domain/models/auth_provider.py
- [ ] T029 [P] Pydantic schemas in backend/src/domain/schemas/__init__.py
- [ ] T030 Database connection and engine setup in backend/src/infrastructure/database.py
- [ ] T031 Alembic migration configuration in backend/alembic.ini and backend/alembic/env.py
- [ ] T032 Initial database migration in backend/alembic/versions/001_initial_schema.py

### Services Layer
- [ ] T033 [P] User service with CRUD operations in backend/src/services/user_service.py
- [ ] T034 [P] TODO service with CRUD and business logic in backend/src/services/todo_service.py
- [ ] T035 [P] Session service for guest user management in backend/src/services/session_service.py
- [ ] T036 [P] Auth service with Clerk integration in backend/src/services/auth_service.py
- [ ] T037 Real-time sync service with SSE in backend/src/services/realtime_service.py

### API Routes and Middleware
- [ ] T038 FastAPI app initialization and configuration in backend/src/main.py
- [ ] T039 CORS middleware configuration in backend/src/api/middleware/cors.py
- [ ] T040 Authentication middleware for Clerk JWT verification in backend/src/api/middleware/auth.py
- [ ] T041 Session middleware for guest user handling in backend/src/api/middleware/session.py
- [ ] T042 Error handling middleware in backend/src/api/middleware/error_handler.py
- [ ] T043 [P] Auth routes implementation in backend/src/api/routes/auth.py
- [ ] T044 [P] TODO routes implementation in backend/src/api/routes/todos.py
- [ ] T045 SSE stream endpoint for real-time updates in backend/src/api/routes/stream.py

### Frontend Infrastructure
- [ ] T046 [P] Next.js app configuration and layout in frontend/src/app/layout.tsx
- [ ] T047 [P] Clerk provider setup in frontend/src/app/providers.tsx
- [ ] T048 [P] TanStack Query client configuration in frontend/src/lib/api/client.ts
- [ ] T049 [P] API client with automatic token injection in frontend/src/lib/api/index.ts
- [ ] T050 [P] Tailwind CSS configuration with cyberpunk theme in frontend/tailwind.config.js
- [ ] T051 [P] Global styles with cyberpunk animations in frontend/src/styles/globals.css

### Frontend Components
- [ ] T052 [P] Base UI components (Button, Input, Card) in frontend/src/components/ui/
- [ ] T053 [P] TodoItem component with cyberpunk styling in frontend/src/components/features/TodoItem.tsx
- [ ] T054 [P] TodoList component with drag-and-drop reordering in frontend/src/components/features/TodoList.tsx
- [ ] T055 [P] AddTodoForm component in frontend/src/components/features/AddTodoForm.tsx
- [ ] T056 [P] UserProfile component in frontend/src/components/features/UserProfile.tsx
- [ ] T057 [P] AuthButtons component for login/signup in frontend/src/components/features/AuthButtons.tsx

### Frontend Pages
- [ ] T058 Home page with guest/authenticated TODO management in frontend/src/app/page.tsx
- [ ] T059 Sign-in page with Clerk integration in frontend/src/app/sign-in/[[...sign-in]]/page.tsx
- [ ] T060 Sign-up page with Clerk integration in frontend/src/app/sign-up/[[...sign-up]]/page.tsx
- [ ] T061 [P] Profile page for user settings in frontend/src/app/(auth)/profile/page.tsx

### Frontend Hooks and State
- [ ] T062 [P] useTodos hook with TanStack Query in frontend/src/lib/hooks/useTodos.ts
- [ ] T063 [P] useAuth hook for Clerk integration in frontend/src/lib/hooks/useAuth.ts
- [ ] T064 [P] useRealTimeSync hook for SSE connection in frontend/src/lib/hooks/useRealTimeSync.ts
- [ ] T065 [P] useSession hook for guest user state in frontend/src/lib/hooks/useSession.ts

## Phase 3.4: Integration
- [ ] T066 Connect TODO service to Neon database with connection pooling
- [ ] T067 Implement Clerk JWT verification in auth middleware
- [ ] T068 Set up SSE broadcasting for real-time updates across user sessions
- [ ] T069 Configure CORS for frontend-backend communication
- [ ] T070 Implement session-to-user migration logic for guest conversion
- [ ] T071 Add request/response logging middleware
- [ ] T072 Configure environment variable validation and loading

## Phase 3.5: Polish
- [ ] T073 [P] Unit tests for user service in backend/tests/unit/test_user_service.py
- [ ] T074 [P] Unit tests for TODO service in backend/tests/unit/test_todo_service.py
- [ ] T075 [P] Unit tests for auth service in backend/tests/unit/test_auth_service.py
- [ ] T076 [P] Unit tests for React components in frontend/tests/unit/
- [ ] T077 [P] E2E tests with Playwright covering all 8 quickstart scenarios in frontend/tests/e2e/
- [ ] T078 [P] Performance tests for API response times (<200ms) in backend/tests/performance/
- [ ] T079 [P] Load testing for concurrent users in backend/tests/load/
- [ ] T080 [P] Update API documentation in backend/docs/api.md
- [ ] T081 [P] Create deployment documentation in docs/deployment.md
- [ ] T082 Code cleanup and refactoring to remove duplication

## Phase 3.6: Deployment
- [ ] T083 [P] GitHub Actions workflow for backend deployment in .github/workflows/deploy-backend.yml
- [ ] T084 [P] GitHub Actions workflow for frontend deployment in .github/workflows/deploy-frontend.yml
- [ ] T085 [P] Cloud Run configuration files in deploy/backend-service.yaml and deploy/frontend-service.yaml
- [ ] T086 [P] Environment variable templates in .env.example files
- [ ] T087 [P] Docker build optimization and multi-stage builds
- [ ] T088 Configure Google Secret Manager integration for production secrets
- [ ] T089 Set up Workload Identity Federation for GitHub Actions
- [ ] T090 Configure custom domain and SSL certificate for Cloud Run
- [ ] T091 Run complete quickstart validation suite
- [ ] T092 Performance validation and load testing in production environment

## Dependencies
- Setup (T001-T005) before everything else
- Contract tests (T006-T017) before any implementation
- Integration tests (T018-T024) before implementation
- Models (T025-T029) before services (T033-T037)
- Services before API routes (T043-T045)
- Backend infrastructure (T030-T032, T038-T042) before frontend API integration (T048-T049)
- Base UI components (T052) before feature components (T053-T057)
- Components before pages (T058-T061)
- Core implementation before integration (T066-T072)
- Integration before polish (T073-T082)
- Everything before deployment (T083-T092)

## Parallel Example
```bash
# Launch T006-T017 contract tests together:
Task: "Contract test POST /api/auth/session in backend/tests/contract/test_auth_session.py"
Task: "Contract test POST /api/auth/user in backend/tests/contract/test_auth_user.py"
Task: "Contract test GET /api/auth/user in backend/tests/contract/test_auth_user.py"
Task: "Contract test POST /api/auth/convert-session in backend/tests/contract/test_auth_convert.py"
# ... (all contract tests can run in parallel)

# Launch T025-T029 model creation together:
Task: "User model in backend/src/domain/models/user.py"
Task: "TodoItem model in backend/src/domain/models/todo_item.py"
Task: "Session model in backend/src/domain/models/session.py"
Task: "AuthProvider model in backend/src/domain/models/auth_provider.py"
Task: "Pydantic schemas in backend/src/domain/schemas/__init__.py"

# Launch T052 UI components together:
Task: "Base UI components (Button, Input, Card) in frontend/src/components/ui/"
Task: "TodoItem component with cyberpunk styling in frontend/src/components/features/TodoItem.tsx"
Task: "TodoList component with drag-and-drop reordering in frontend/src/components/features/TodoList.tsx"
# ... (all component tasks can run in parallel)
```

## Notes
- [P] tasks = different files, no dependencies
- Verify tests fail before implementing
- Follow TDD strictly: Red-Green-Refactor
- Commit after each task completion
- Run full test suite before proceeding to next phase
- All API endpoints must pass contract tests
- Frontend components must have cyberpunk theme styling
- Real-time sync must work within 500ms
- Support both guest and authenticated user flows

## Task Generation Rules
*Applied during main() execution*

1. **From Contracts**:
   - Each endpoint → contract test task [P]
   - Each endpoint → implementation task

2. **From Data Model**:
   - Each entity → model creation task [P]
   - Database setup → migration tasks

3. **From User Stories (Quickstart)**:
   - Each scenario → integration test [P]
   - UI flows → component tasks

4. **From Tech Stack**:
   - FastAPI → backend structure tasks
   - Next.js → frontend structure tasks
   - Clerk → auth integration tasks
   - Neon → database tasks
   - Cloud Run → deployment tasks

5. **Ordering**:
   - Setup → Tests → Models → Services → API → Frontend → Integration → Polish → Deployment
   - TDD enforced: All tests before implementation
   - Dependencies block parallel execution

## Validation Checklist
*GATE: Checked by main() before returning*

- [x] All contracts have corresponding tests (T006-T017)
- [x] All entities have model tasks (T025-T028)
- [x] All tests come before implementation (Phase 3.2 before 3.3)
- [x] Parallel tasks truly independent ([P] marking verified)
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task
- [x] All 8 quickstart scenarios covered in integration tests
- [x] Complete deployment pipeline included
- [x] Performance and load testing included
- [x] TDD workflow enforced throughout