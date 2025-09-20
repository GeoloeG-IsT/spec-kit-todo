# Deployment Guide

## Prerequisites

- Google Cloud Platform account with billing enabled
- GitHub repository with the code
- Neon database account
- Clerk account for authentication
- Domain name (optional, for custom domain)

## Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  GitHub Actions ├────►│  Cloud Run      ├────►│  Neon Database  │
│                 │     │  (Backend)      │     │  (PostgreSQL)   │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                                 │
                        ┌────────▼────────┐     ┌─────────────────┐
                        │                 │     │                 │
                        │  Cloud Run      │────►│  Clerk Auth     │
                        │  (Frontend)     │     │                 │
                        └─────────────────┘     └─────────────────┘
```

## Step 1: Database Setup (Neon)

1. **Create Neon Project**
   ```bash
   # Install Neon CLI
   npm install -g neon

   # Login to Neon
   neon auth

   # Create project
   neon projects create todo-app --region us-west-2
   ```

2. **Create Database Branches**
   ```bash
   # Production branch
   neon branches create --name production

   # Staging branch
   neon branches create --name staging

   # Get connection strings
   neon connection-string production
   neon connection-string staging
   ```

3. **Run Migrations**
   ```bash
   # Set database URL
   export DATABASE_URL=$(neon connection-string production)

   # Run migrations
   cd backend
   alembic upgrade head
   ```

## Step 2: Google Cloud Setup

1. **Install and Configure gcloud CLI**
   ```bash
   # Install gcloud
   curl https://sdk.cloud.google.com | bash

   # Initialize
   gcloud init

   # Set project
   gcloud config set project YOUR_PROJECT_ID
   ```

2. **Enable Required APIs**
   ```bash
   gcloud services enable \
     cloudrun.googleapis.com \
     artifactregistry.googleapis.com \
     cloudbuild.googleapis.com \
     secretmanager.googleapis.com
   ```

3. **Create Artifact Registry Repository**
   ```bash
   gcloud artifacts repositories create todo-app \
     --repository-format=docker \
     --location=us-central1 \
     --description="TODO App Docker images"
   ```

4. **Set Up Secret Manager**
   ```bash
   # Create secrets
   echo -n "your-database-url" | gcloud secrets create DATABASE_URL --data-file=-
   echo -n "your-clerk-secret" | gcloud secrets create CLERK_SECRET_KEY --data-file=-
   echo -n "your-clerk-public" | gcloud secrets create CLERK_PUBLISHABLE_KEY --data-file=-
   ```

## Step 3: GitHub Actions Setup

1. **Create Service Account**
   ```bash
   # Create service account
   gcloud iam service-accounts create github-actions \
     --display-name="GitHub Actions"

   # Grant permissions
   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
     --member="serviceAccount:github-actions@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
     --role="roles/run.admin"

   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
     --member="serviceAccount:github-actions@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
     --role="roles/artifactregistry.writer"

   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
     --member="serviceAccount:github-actions@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
     --role="roles/secretmanager.secretAccessor"
   ```

2. **Set Up Workload Identity Federation**
   ```bash
   # Create identity pool
   gcloud iam workload-identity-pools create github \
     --location="global" \
     --display-name="GitHub Actions Pool"

   # Create provider
   gcloud iam workload-identity-pools providers create-oidc github \
     --location="global" \
     --workload-identity-pool="github" \
     --display-name="GitHub" \
     --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
     --issuer-uri="https://token.actions.githubusercontent.com"

   # Bind service account
   gcloud iam service-accounts add-iam-policy-binding \
     github-actions@YOUR_PROJECT_ID.iam.gserviceaccount.com \
     --role="roles/iam.workloadIdentityUser" \
     --member="principalSet://iam.googleapis.com/projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github/attribute.repository/YOUR_GITHUB_ORG/YOUR_REPO"
   ```

3. **Add GitHub Secrets**

   In your GitHub repository settings, add these secrets:
   - `GCP_PROJECT_ID`: Your GCP project ID
   - `GCP_REGION`: us-central1
   - `WIF_PROVIDER`: projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github/providers/github
   - `WIF_SERVICE_ACCOUNT`: github-actions@YOUR_PROJECT_ID.iam.gserviceaccount.com

## Step 4: Deploy Backend

1. **Build and Push Docker Image**
   ```bash
   cd backend

   # Build image
   docker build -t todo-backend .

   # Tag for Artifact Registry
   docker tag todo-backend \
     us-central1-docker.pkg.dev/YOUR_PROJECT_ID/todo-app/backend:latest

   # Push to registry
   docker push \
     us-central1-docker.pkg.dev/YOUR_PROJECT_ID/todo-app/backend:latest
   ```

2. **Deploy to Cloud Run**
   ```bash
   gcloud run deploy todo-backend \
     --image us-central1-docker.pkg.dev/YOUR_PROJECT_ID/todo-app/backend:latest \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars="CORS_ORIGINS=https://your-frontend-url.com" \
     --set-secrets="DATABASE_URL=DATABASE_URL:latest,CLERK_SECRET_KEY=CLERK_SECRET_KEY:latest" \
     --min-instances=1 \
     --max-instances=10 \
     --memory=512Mi \
     --cpu=1
   ```

## Step 5: Deploy Frontend

1. **Build and Push Docker Image**
   ```bash
   cd frontend

   # Build image
   docker build -t todo-frontend \
     --build-arg NEXT_PUBLIC_API_URL=https://todo-backend-xxxxx-uc.a.run.app \
     --build-arg NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_live_xxx .

   # Tag for Artifact Registry
   docker tag todo-frontend \
     us-central1-docker.pkg.dev/YOUR_PROJECT_ID/todo-app/frontend:latest

   # Push to registry
   docker push \
     us-central1-docker.pkg.dev/YOUR_PROJECT_ID/todo-app/frontend:latest
   ```

2. **Deploy to Cloud Run**
   ```bash
   gcloud run deploy todo-frontend \
     --image us-central1-docker.pkg.dev/YOUR_PROJECT_ID/todo-app/frontend:latest \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --min-instances=1 \
     --max-instances=10 \
     --memory=256Mi \
     --cpu=1
   ```

## Step 6: Configure Custom Domain (Optional)

1. **Map Custom Domain**
   ```bash
   # For backend
   gcloud run domain-mappings create \
     --service todo-backend \
     --domain api.yourdomain.com \
     --region us-central1

   # For frontend
   gcloud run domain-mappings create \
     --service todo-frontend \
     --domain yourdomain.com \
     --region us-central1
   ```

2. **Update DNS Records**

   Add the provided DNS records to your domain provider:
   - A/AAAA records for the IP addresses
   - CNAME records if provided

## Step 7: GitHub Actions Workflow

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Cloud Run

on:
  push:
    branches: [main]
  workflow_dispatch:

env:
  PROJECT_ID: ${{ secrets.GCP_PROJECT_ID }}
  REGION: ${{ secrets.GCP_REGION }}
  BACKEND_SERVICE: todo-backend
  FRONTEND_SERVICE: todo-frontend

jobs:
  deploy-backend:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      id-token: write

    steps:
      - uses: actions/checkout@v4

      - id: auth
        uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: ${{ secrets.WIF_PROVIDER }}
          service_account: ${{ secrets.WIF_SERVICE_ACCOUNT }}

      - name: Set up Cloud SDK
        uses: google-github-actions/setup-gcloud@v2

      - name: Configure Docker
        run: gcloud auth configure-docker us-central1-docker.pkg.dev

      - name: Build and Push Backend
        run: |
          cd backend
          docker build -t us-central1-docker.pkg.dev/$PROJECT_ID/todo-app/backend:$GITHUB_SHA .
          docker push us-central1-docker.pkg.dev/$PROJECT_ID/todo-app/backend:$GITHUB_SHA

      - name: Deploy Backend to Cloud Run
        run: |
          gcloud run deploy $BACKEND_SERVICE \
            --image us-central1-docker.pkg.dev/$PROJECT_ID/todo-app/backend:$GITHUB_SHA \
            --region $REGION \
            --platform managed

  deploy-frontend:
    runs-on: ubuntu-latest
    needs: deploy-backend
    permissions:
      contents: read
      id-token: write

    steps:
      - uses: actions/checkout@v4

      - id: auth
        uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: ${{ secrets.WIF_PROVIDER }}
          service_account: ${{ secrets.WIF_SERVICE_ACCOUNT }}

      - name: Set up Cloud SDK
        uses: google-github-actions/setup-gcloud@v2

      - name: Configure Docker
        run: gcloud auth configure-docker us-central1-docker.pkg.dev

      - name: Get Backend URL
        id: backend-url
        run: |
          URL=$(gcloud run services describe $BACKEND_SERVICE --region $REGION --format 'value(status.url)')
          echo "url=$URL" >> $GITHUB_OUTPUT

      - name: Build and Push Frontend
        run: |
          cd frontend
          docker build \
            --build-arg NEXT_PUBLIC_API_URL=${{ steps.backend-url.outputs.url }} \
            --build-arg NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=${{ secrets.CLERK_PUBLISHABLE_KEY }} \
            -t us-central1-docker.pkg.dev/$PROJECT_ID/todo-app/frontend:$GITHUB_SHA .
          docker push us-central1-docker.pkg.dev/$PROJECT_ID/todo-app/frontend:$GITHUB_SHA

      - name: Deploy Frontend to Cloud Run
        run: |
          gcloud run deploy $FRONTEND_SERVICE \
            --image us-central1-docker.pkg.dev/$PROJECT_ID/todo-app/frontend:$GITHUB_SHA \
            --region $REGION \
            --platform managed
```

## Monitoring and Maintenance

### Cloud Run Metrics
```bash
# View service logs
gcloud run services logs read todo-backend --region us-central1

# View metrics
gcloud monitoring metrics-descriptors list --filter="metric.type:run.googleapis.com"
```

### Database Monitoring
```bash
# Check database metrics
neon branches list
neon branches show production --stats
```

### Rollback Procedure
```bash
# List revisions
gcloud run revisions list --service todo-backend --region us-central1

# Rollback to previous revision
gcloud run services update-traffic todo-backend \
  --to-revisions PREVIOUS_REVISION=100 \
  --region us-central1
```

### Scaling Configuration
```bash
# Update scaling limits
gcloud run services update todo-backend \
  --min-instances=2 \
  --max-instances=20 \
  --concurrency=100 \
  --region us-central1
```

## Security Checklist

- [ ] All secrets stored in Secret Manager
- [ ] HTTPS enforced on all endpoints
- [ ] CORS configured for production domains only
- [ ] Database connections use SSL
- [ ] Rate limiting enabled
- [ ] Security headers configured
- [ ] Regular dependency updates
- [ ] Vulnerability scanning enabled
- [ ] Audit logs enabled
- [ ] Backup strategy implemented

## Cost Optimization

1. **Use Cloud Run minimum instances wisely**
   - Set to 0 for development
   - Set to 1-2 for production based on traffic

2. **Optimize Docker images**
   - Use multi-stage builds
   - Minimize layer size
   - Use .dockerignore

3. **Database optimization**
   - Use Neon's auto-suspend feature
   - Configure appropriate compute size
   - Regular cleanup of old data

4. **CDN for static assets**
   - Use Cloud CDN for frontend assets
   - Cache API responses where appropriate

## Troubleshooting

### Common Issues

1. **502 Bad Gateway**
   - Check Cloud Run logs: `gcloud run services logs read`
   - Verify environment variables
   - Check database connectivity

2. **CORS errors**
   - Verify CORS_ORIGINS environment variable
   - Check API URL in frontend configuration

3. **Authentication failures**
   - Verify Clerk keys are correct
   - Check JWT validation logic
   - Ensure clock sync between services

4. **Database connection issues**
   - Verify DATABASE_URL is correct
   - Check Neon branch status
   - Ensure IP allowlisting if configured

### Support Resources

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Neon Documentation](https://neon.tech/docs)
- [Clerk Documentation](https://clerk.dev/docs)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)