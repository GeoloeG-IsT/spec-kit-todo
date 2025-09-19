# Research: TODO List App Technical Decisions

**Date**: 2025-01-19
**Feature**: TODO List App with Authentication and Real-time Sync

## 1. Clerk Authentication Setup

### Decision
Use Clerk's hosted authentication with JWT token verification between FastAPI backend and Next.js frontend.

### Rationale
- Clerk provides native SDKs for both Next.js and Python/FastAPI
- Handles OAuth complexity, token refresh, and session management automatically
- Development mode uses shared credentials (zero configuration)
- Production-ready with enterprise security features

### Alternatives Considered
- **Auth0**: More expensive, complex setup for small projects
- **NextAuth.js + Custom Backend**: Requires building JWT handling, OAuth flows manually
- **Supabase Auth**: Tightly coupled with Supabase database, less flexible

### Implementation Details
```python
# FastAPI backend - JWT verification
from clerk_backend_api import Clerk
from fastapi import Depends, HTTPException
from jose import jwt

clerk = Clerk(bearer_auth="sk_test_...")

async def verify_token(authorization: str = Header()):
    token = authorization.replace("Bearer ", "")
    try:
        # Verify JWT using Clerk's JWKS endpoint
        payload = jwt.decode(token, clerk.get_jwks(), algorithms=["RS256"])
        return payload
    except:
        raise HTTPException(401, "Invalid token")
```

```typescript
// Next.js frontend - Clerk provider
import { ClerkProvider } from '@clerk/nextjs'
import { useAuth } from '@clerk/nextjs'

// Automatic token injection for API calls
const { getToken } = useAuth()
const token = await getToken()
```

**Environment Variables**:
- `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`
- `CLERK_SECRET_KEY`
- `NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in`
- `NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up`

## 2. Neon Database Local Development

### Decision
Use Neon database branching with direct cloud connection for local development.

### Rationale
- Database branching allows creating isolated dev environments like Git branches
- No local PostgreSQL setup required
- Built-in connection pooling with PgBouncer
- Instant provisioning with copy-on-write

### Alternatives Considered
- **Local PostgreSQL + Docker**: Requires Docker setup, data sync issues
- **Supabase**: Less flexible branching, tighter platform coupling
- **PlanetScale**: MySQL instead of PostgreSQL, different feature set

### Implementation Details
```python
# SQLModel connection with Neon
from sqlmodel import create_engine, Session
import os

# Neon connection string with pooling
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user:pass@ep-xxx.region.aws.neon.tech/dbname?sslmode=require"
)

# Use connection pooling for serverless
engine = create_engine(
    DATABASE_URL,
    connect_args={
        "server_settings": {"jit": "off"},
        "command_timeout": 10,
        "options": "-c statement_timeout=10000"
    },
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)
```

**Branching Strategy**:
```bash
# Create development branch
neon branches create --name dev/feature-auth --parent main

# Get connection string for branch
neon connection-string dev/feature-auth
```

## 3. GCP Cloud Run Deployment

### Decision
Deploy to Cloud Run using GitHub Actions with Artifact Registry and Workload Identity Federation.

### Rationale
- Fully managed serverless platform with automatic scaling
- Native container support with no vendor lock-in
- Workload Identity Federation eliminates service account keys
- Supports streaming responses for SSE

### Alternatives Considered
- **Vercel**: Limited backend support, vendor lock-in
- **Railway**: Simpler but less control over infrastructure
- **GKE**: Overkill for this project size

### Implementation Details
```yaml
# .github/workflows/deploy.yml
name: Deploy to Cloud Run

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      id-token: write

    steps:
      - uses: actions/checkout@v3

      - id: auth
        uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: ${{ secrets.WIF_PROVIDER }}
          service_account: ${{ secrets.WIF_SERVICE_ACCOUNT }}

      - name: Build and Push
        run: |
          gcloud builds submit --tag gcr.io/$PROJECT/backend
          gcloud builds submit --tag gcr.io/$PROJECT/frontend

      - name: Deploy
        run: |
          gcloud run deploy backend \
            --image gcr.io/$PROJECT/backend \
            --region us-central1 \
            --allow-unauthenticated
```

**Cloud Run Configuration**:
```yaml
# cloud-run.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: todo-backend
spec:
  template:
    metadata:
      annotations:
        run.googleapis.com/execution-environment: gen2
        run.googleapis.com/cpu-throttling: "false"
    spec:
      containerConcurrency: 1000
      timeoutSeconds: 300
      containers:
        - image: gcr.io/project/backend
          env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: database-url
                  key: latest
```

## 4. Real-time Sync Implementation

### Decision
Use Server-Sent Events (SSE) instead of WebSockets for real-time updates.

### Rationale
- SSE works over standard HTTP/2 (Cloud Run friendly)
- Simpler than WebSockets for unidirectional updates
- Automatic reconnection built into EventSource API
- Better firewall and proxy traversal

### Alternatives Considered
- **WebSockets**: Cloud Run support limited, complex state management
- **Polling**: Inefficient, higher latency
- **Firebase Realtime Database**: Vendor lock-in, separate data store

### Implementation Details
```python
# FastAPI SSE endpoint
from fastapi import FastAPI
from sse_starlette.sse import EventSourceResponse
import asyncio
import json

app = FastAPI()

@app.get("/api/todos/stream")
async def todo_stream(user_id: str = Depends(get_current_user)):
    async def event_generator():
        while True:
            # Check for updates
            updates = await check_todo_updates(user_id)
            if updates:
                yield {
                    "event": "update",
                    "data": json.dumps(updates)
                }
            await asyncio.sleep(1)

    return EventSourceResponse(event_generator())
```

```typescript
// Frontend SSE consumption with TanStack Query
import { useQueryClient } from '@tanstack/react-query'

function useTodoStream() {
  const queryClient = useQueryClient()

  useEffect(() => {
    const eventSource = new EventSource('/api/todos/stream')

    eventSource.addEventListener('update', (event) => {
      const data = JSON.parse(event.data)
      // Invalidate and refetch affected queries
      queryClient.invalidateQueries(['todos'])
    })

    return () => eventSource.close()
  }, [])
}
```

## 5. OAuth Provider Configuration

### Decision
Configure OAuth providers through Clerk's dashboard with custom credentials for production.

### Rationale
- Unified OAuth management through single provider
- Automatic token refresh and session handling
- Development uses Clerk's shared OAuth apps
- Production allows custom branding and scopes

### Alternatives Considered
- **Direct OAuth Implementation**: Complex, security risks
- **Passport.js**: Backend-only, no frontend integration
- **Supabase Auth**: Limited provider customization

### Implementation Details

**Google OAuth Setup**:
1. Create project in Google Cloud Console
2. Enable Google+ API
3. Create OAuth 2.0 credentials
4. Add redirect URI: `https://YOUR_DOMAIN.clerk.accounts.dev/v1/oauth_callback`
5. Required scopes: `openid`, `email`, `profile`

**GitHub OAuth Setup**:
1. Create OAuth App in GitHub Settings
2. Authorization callback URL: `https://YOUR_DOMAIN.clerk.accounts.dev/v1/oauth_callback`
3. Required scopes: `read:user`, `user:email`

**LinkedIn OAuth Setup**:
1. Create app in LinkedIn Developers
2. Add redirect URL: `https://YOUR_DOMAIN.clerk.accounts.dev/v1/oauth_callback`
3. Required scopes: `r_liteprofile`, `r_emailaddress`

**Clerk Configuration**:
```javascript
// Environment variables
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...

// OAuth enable in Clerk Dashboard
// Development: Uses Clerk's shared credentials
// Production: Add custom OAuth credentials
```

## Summary of Technical Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Backend Framework | FastAPI | Async support, automatic OpenAPI docs |
| ORM | SQLModel | Type safety, Pydantic integration |
| Database | Neon PostgreSQL | Serverless, branching, built-in pooling |
| Authentication | Clerk | Complete auth solution, OAuth support |
| Frontend Framework | Next.js 14 | App router, RSC, excellent DX |
| UI Library | React 18 + TailwindCSS | Component composition, utility-first CSS |
| State Management | TanStack Query | Server state sync, caching |
| Real-time Updates | Server-Sent Events | Cloud Run compatible, simpler than WS |
| Deployment | GCP Cloud Run | Serverless, auto-scaling, containers |
| CI/CD | GitHub Actions | Native integration, Workload Identity |
| Container Registry | Artifact Registry | Replacing Container Registry |
| Secret Management | Google Secret Manager | Secure, versioned, audited |

## Local Development Setup

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev

# Database
neon branches create --name dev/local
export DATABASE_URL=$(neon connection-string dev/local)

# Environment
cp .env.example .env.local
# Add Clerk keys and Neon connection string
```

## Production Deployment Checklist

- [ ] Set up GCP project with billing
- [ ] Enable required APIs (Cloud Run, Artifact Registry, Secret Manager)
- [ ] Configure Workload Identity Federation for GitHub Actions
- [ ] Create production Neon database
- [ ] Set up custom OAuth apps (Google, GitHub, LinkedIn)
- [ ] Configure Clerk production instance
- [ ] Set up custom domain with Cloud Run
- [ ] Configure GitHub Actions secrets
- [ ] Enable Cloud Run continuous deployment

This research provides a solid foundation for implementing the TODO list application with modern, scalable, and developer-friendly technologies.