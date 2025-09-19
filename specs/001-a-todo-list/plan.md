# Implementation Plan: TODO List App

**Branch**: `001-a-todo-list` | **Date**: 2025-01-19 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-a-todo-list/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → If not found: ERROR "No feature spec at {path}"
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detect Project Type from context (web=frontend+backend, mobile=app+api)
   → Set Structure Decision based on project type
3. Fill the Constitution Check section based on the content of the constitution document.
4. Evaluate Constitution Check section below
   → If violations exist: Document in Complexity Tracking
   → If no justification possible: ERROR "Simplify approach first"
   → Update Progress Tracking: Initial Constitution Check
5. Execute Phase 0 → research.md
   → If NEEDS CLARIFICATION remain: ERROR "Resolve unknowns"
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file (e.g., `CLAUDE.md` for Claude Code, `.github/copilot-instructions.md` for GitHub Copilot, `GEMINI.md` for Gemini CLI, `QWEN.md` for Qwen Code or `AGENTS.md` for opencode).
7. Re-evaluate Constitution Check section
   → If new violations: Refactor design, return to Phase 1
   → Update Progress Tracking: Post-Design Constitution Check
8. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
9. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
A full-stack TODO list application with guest and authenticated user modes, featuring real-time sync, OAuth integration (Google, GitHub, LinkedIn), and a cyberpunk-themed UI. Backend uses FastAPI with SQLModel ORM, frontend uses Next.js with React and TailwindCSS, authentication via Clerk, and PostgreSQL database hosted on Neon. Deployment targets GCP Cloud Run with GitHub Actions CI/CD.

## Technical Context
**Language/Version**: Python 3.11 (backend), TypeScript/Node.js 20+ (frontend)
**Primary Dependencies**: FastAPI, SQLModel, httpx, Pydantic (backend) | Next.js 14+, React 18+, TailwindCSS, TanStack Query (frontend) | Clerk (auth)
**Storage**: PostgreSQL with Neon (cloud-native serverless Postgres)
**Testing**: pytest, pytest-asyncio (backend) | Jest, React Testing Library, Playwright (frontend)
**Target Platform**: GCP Cloud Run (containerized deployment)
**Project Type**: web (frontend + backend)
**Performance Goals**: <200ms API response time, real-time sync within 500ms
**Constraints**: Stateless containers for Cloud Run, WebSocket support via Cloud Run streaming
**Scale/Scope**: Support 10k concurrent users, unlimited TODO items per user

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- ✅ **Clean Architecture**: Separating frontend/backend with clear API boundaries, domain logic in services layer
- ✅ **Domain-Driven Design**: TODO and User as core domain entities with clear bounded contexts
- ✅ **Test-First Development**: Will write contract tests before implementation
- ✅ **Library-First Approach**: Each feature component will be modular and reusable
- ✅ **SOLID Principles**: Using dependency injection, interface segregation via API contracts
- ✅ **DRY**: Shared types/schemas between frontend and backend via OpenAPI
- ✅ **KISS**: Using established frameworks rather than custom solutions
- ✅ **YAGNI**: Only implementing specified features, no speculative additions

## Project Structure

### Documentation (this feature)
```
specs/001-a-todo-list/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
# Option 2: Web application (frontend + backend detected)
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
.github/
├── workflows/
│   └── deploy.yml       # GitHub Actions CI/CD
docker/
├── backend.Dockerfile
└── frontend.Dockerfile
docker-compose.yml       # Local development
```

**Structure Decision**: Option 2 - Web application structure (frontend + backend)

## Phase 0: Outline & Research
1. **Extract unknowns from Technical Context** above:
   - Clerk authentication setup for local development
   - Neon database connection for local development
   - GCP Cloud Run deployment configuration
   - Real-time sync implementation approach
   - OAuth provider configuration

2. **Generate and dispatch research agents**:
   ```
   Task 1: "Research Clerk authentication setup with FastAPI backend and Next.js frontend"
   Task 2: "Research Neon PostgreSQL local development setup and connection pooling"
   Task 3: "Research GCP Cloud Run deployment with GitHub Actions for containerized apps"
   Task 4: "Research real-time sync patterns with FastAPI WebSockets and TanStack Query"
   Task 5: "Research OAuth integration with Clerk for Google, GitHub, LinkedIn providers"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with all NEEDS CLARIFICATION resolved

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md`:
   - User entity with auth provider links
   - TodoItem entity with user association
   - Session entity for guest users
   - Authentication tokens and refresh logic

2. **Generate API contracts** from functional requirements:
   - Auth endpoints (signup, login, logout, OAuth callbacks)
   - TODO CRUD endpoints (create, read, update, delete, list)
   - User profile endpoints
   - WebSocket endpoint for real-time sync
   - Output OpenAPI schema to `/contracts/`

3. **Generate contract tests** from contracts:
   - Auth flow tests
   - TODO operations tests
   - Guest session tests
   - Real-time sync tests

4. **Extract test scenarios** from user stories:
   - Guest user creates and manages TODOs
   - User signs up and persists TODOs
   - Guest converts to registered user
   - Multi-device sync scenario

5. **Update agent file incrementally**:
   - Run `.specify/scripts/bash/update-agent-context.sh claude`
   - Add FastAPI, SQLModel, Clerk, Neon context
   - Document project structure

**Output**: data-model.md, /contracts/*, failing tests, quickstart.md, CLAUDE.md

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Setup tasks: Docker, dependencies, environment variables
- Database tasks: Models, migrations, connection setup
- Auth tasks: Clerk integration, JWT handling, OAuth setup
- API tasks: FastAPI routes, middleware, error handling
- Frontend tasks: Components, pages, API client
- Integration tasks: Real-time sync, session management
- Testing tasks: Contract tests, E2E tests
- Deployment tasks: Dockerfiles, GitHub Actions, Cloud Run config

**Ordering Strategy**:
- Infrastructure setup first
- Backend before frontend
- Auth before business logic
- Tests before implementation (TDD)
- Deployment configuration last

**Estimated Output**: 35-40 numbered, ordered tasks in tasks.md

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)
**Phase 4**: Implementation (execute tasks.md following constitutional principles)
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

No violations identified. All architectural decisions align with constitutional principles.

## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved
- [x] Complexity deviations documented (none found)

---
*Based on Constitution v1.0.0 - See `.specify/memory/constitution.md`*