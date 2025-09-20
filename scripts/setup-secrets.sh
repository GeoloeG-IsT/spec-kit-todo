#!/bin/bash
# Setup Google Secret Manager secrets for production deployment

set -e

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-your-project-id}"
REGION="${GCP_REGION:-us-central1}"

echo "Setting up secrets for project: $PROJECT_ID"

# Check if gcloud is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "Error: No active gcloud authentication found. Please run 'gcloud auth login'"
    exit 1
fi

# Set the project
gcloud config set project "$PROJECT_ID"

# Function to create or update secret
create_or_update_secret() {
    local secret_name="$1"
    local secret_value="$2"
    local description="$3"

    echo "Processing secret: $secret_name"

    if gcloud secrets describe "$secret_name" &>/dev/null; then
        echo "  Secret $secret_name exists, adding new version..."
        echo "$secret_value" | gcloud secrets versions add "$secret_name" --data-file=-
    else
        echo "  Creating new secret: $secret_name"
        echo "$secret_value" | gcloud secrets create "$secret_name" \
            --data-file=- \
            --labels="app=todo,environment=production" \
            --replication-policy="automatic"
    fi
}

# Backend secrets
echo "Creating backend secrets..."

# Database URL
if [ -z "$DATABASE_URL" ]; then
    echo "Warning: DATABASE_URL environment variable not set"
    echo "Please set it to your Neon database connection string"
    read -p "Enter DATABASE_URL: " DATABASE_URL
fi
create_or_update_secret "database-url" "$DATABASE_URL" "Neon PostgreSQL connection string"

# Clerk Secret Key
if [ -z "$CLERK_SECRET_KEY" ]; then
    echo "Warning: CLERK_SECRET_KEY environment variable not set"
    read -s -p "Enter Clerk Secret Key: " CLERK_SECRET_KEY
    echo
fi
create_or_update_secret "clerk-secret-key" "$CLERK_SECRET_KEY" "Clerk authentication secret key"

# Clerk Publishable Key
if [ -z "$CLERK_PUBLISHABLE_KEY" ]; then
    echo "Warning: CLERK_PUBLISHABLE_KEY environment variable not set"
    read -p "Enter Clerk Publishable Key: " CLERK_PUBLISHABLE_KEY
fi
create_or_update_secret "clerk-publishable-key" "$CLERK_PUBLISHABLE_KEY" "Clerk authentication publishable key"

# Frontend secrets
echo "Creating frontend secrets..."

# Next.js Clerk Publishable Key (can be same as backend)
create_or_update_secret "next-public-clerk-publishable-key" "$CLERK_PUBLISHABLE_KEY" "Clerk publishable key for Next.js"

# API URL for frontend
BACKEND_URL="${BACKEND_URL:-https://todo-backend-hash-uc.a.run.app}"
create_or_update_secret "next-public-api-url" "$BACKEND_URL" "Backend API URL for frontend"

# Set up IAM permissions for Cloud Run
echo "Setting up IAM permissions..."

# Get the Compute Engine default service account
COMPUTE_SA=$(gcloud iam service-accounts list --format="value(email)" --filter="displayName:Compute Engine default service account")

if [ -n "$COMPUTE_SA" ]; then
    echo "Granting Secret Manager access to: $COMPUTE_SA"

    # Grant access to secrets
    for secret in "database-url" "clerk-secret-key" "clerk-publishable-key" "next-public-clerk-publishable-key" "next-public-api-url"; do
        gcloud secrets add-iam-policy-binding "$secret" \
            --member="serviceAccount:$COMPUTE_SA" \
            --role="roles/secretmanager.secretAccessor"
    done
else
    echo "Warning: Could not find Compute Engine default service account"
    echo "You may need to manually grant Secret Manager access to your Cloud Run service accounts"
fi

# Create service account for backend
echo "Creating service account for backend..."
BACKEND_SA="todo-backend-sa@$PROJECT_ID.iam.gserviceaccount.com"

if ! gcloud iam service-accounts describe "$BACKEND_SA" &>/dev/null; then
    gcloud iam service-accounts create todo-backend-sa \
        --display-name="TODO Backend Service Account" \
        --description="Service account for TODO backend application"
fi

# Grant permissions to backend service account
for secret in "database-url" "clerk-secret-key" "clerk-publishable-key"; do
    gcloud secrets add-iam-policy-binding "$secret" \
        --member="serviceAccount:$BACKEND_SA" \
        --role="roles/secretmanager.secretAccessor"
done

# Create service account for frontend
echo "Creating service account for frontend..."
FRONTEND_SA="todo-frontend-sa@$PROJECT_ID.iam.gserviceaccount.com"

if ! gcloud iam service-accounts describe "$FRONTEND_SA" &>/dev/null; then
    gcloud iam service-accounts create todo-frontend-sa \
        --display-name="TODO Frontend Service Account" \
        --description="Service account for TODO frontend application"
fi

# Grant permissions to frontend service account
for secret in "next-public-clerk-publishable-key" "next-public-api-url"; do
    gcloud secrets add-iam-policy-binding "$secret" \
        --member="serviceAccount:$FRONTEND_SA" \
        --role="roles/secretmanager.secretAccessor"
done

# Enable required APIs
echo "Enabling required Google Cloud APIs..."
gcloud services enable \
    secretmanager.googleapis.com \
    run.googleapis.com \
    artifactregistry.googleapis.com \
    cloudbuild.googleapis.com \
    iamcredentials.googleapis.com

echo "✅ Secret Manager setup completed!"
echo ""
echo "Secrets created:"
echo "  - database-url"
echo "  - clerk-secret-key"
echo "  - clerk-publishable-key"
echo "  - next-public-clerk-publishable-key"
echo "  - next-public-api-url"
echo ""
echo "Service accounts created:"
echo "  - $BACKEND_SA"
echo "  - $FRONTEND_SA"
echo ""
echo "Next steps:"
echo "1. Update your GitHub repository secrets with these values"
echo "2. Update the Cloud Run service configurations to use these secrets"
echo "3. Deploy your applications!"