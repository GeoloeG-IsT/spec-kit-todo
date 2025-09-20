#!/bin/bash
# Setup Workload Identity Federation for GitHub Actions

set -e

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-your-project-id}"
PROJECT_NUMBER="${GCP_PROJECT_NUMBER:-your-project-number}"
GITHUB_OWNER="${GITHUB_OWNER:-your-github-username}"
GITHUB_REPO="${GITHUB_REPO:-spec-kit-todo}"
POOL_ID="github-actions-pool"
PROVIDER_ID="github-actions-provider"
SERVICE_ACCOUNT_ID="github-actions-sa"

echo "Setting up Workload Identity Federation for GitHub Actions"
echo "Project ID: $PROJECT_ID"
echo "Project Number: $PROJECT_NUMBER"
echo "GitHub Owner: $GITHUB_OWNER"
echo "GitHub Repo: $GITHUB_REPO"

# Check if gcloud is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "Error: No active gcloud authentication found. Please run 'gcloud auth login'"
    exit 1
fi

# Set the project
gcloud config set project "$PROJECT_ID"

# Enable required APIs
echo "Enabling required APIs..."
gcloud services enable \
    iamcredentials.googleapis.com \
    cloudresourcemanager.googleapis.com \
    sts.googleapis.com

# Create service account for GitHub Actions
echo "Creating service account for GitHub Actions..."
SERVICE_ACCOUNT_EMAIL="$SERVICE_ACCOUNT_ID@$PROJECT_ID.iam.gserviceaccount.com"

if ! gcloud iam service-accounts describe "$SERVICE_ACCOUNT_EMAIL" &>/dev/null; then
    gcloud iam service-accounts create "$SERVICE_ACCOUNT_ID" \
        --display-name="GitHub Actions Service Account" \
        --description="Service account for GitHub Actions CI/CD"
fi

# Grant necessary roles to the service account
echo "Granting roles to service account..."
ROLES=(
    "roles/run.admin"
    "roles/storage.admin"
    "roles/artifactregistry.admin"
    "roles/cloudsql.client"
    "roles/secretmanager.secretAccessor"
    "roles/iam.serviceAccountUser"
    "roles/cloudbuild.builds.builder"
)

for role in "${ROLES[@]}"; do
    echo "  Granting $role..."
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
        --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
        --role="$role"
done

# Create Workload Identity Pool
echo "Creating Workload Identity Pool..."
POOL_NAME="projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/$POOL_ID"

if ! gcloud iam workload-identity-pools describe "$POOL_ID" --location="global" &>/dev/null; then
    gcloud iam workload-identity-pools create "$POOL_ID" \
        --location="global" \
        --display-name="GitHub Actions Pool" \
        --description="Pool for GitHub Actions"
fi

# Create Workload Identity Provider
echo "Creating Workload Identity Provider..."
PROVIDER_NAME="$POOL_NAME/providers/$PROVIDER_ID"

if ! gcloud iam workload-identity-pools providers describe "$PROVIDER_ID" \
    --workload-identity-pool="$POOL_ID" \
    --location="global" &>/dev/null; then

    gcloud iam workload-identity-pools providers create-oidc "$PROVIDER_ID" \
        --workload-identity-pool="$POOL_ID" \
        --location="global" \
        --issuer-uri="https://token.actions.githubusercontent.com" \
        --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
        --attribute-condition="assertion.repository=='$GITHUB_OWNER/$GITHUB_REPO'"
fi

# Allow the GitHub Actions to impersonate the service account
echo "Setting up impersonation permissions..."
gcloud iam service-accounts add-iam-policy-binding "$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/iam.workloadIdentityUser" \
    --member="principalSet://iam.googleapis.com/$POOL_NAME/attribute.repository/$GITHUB_OWNER/$GITHUB_REPO"

# Display the configuration for GitHub Actions
echo ""
echo "✅ Workload Identity Federation setup completed!"
echo ""
echo "Add these secrets to your GitHub repository:"
echo "  GCP_PROJECT_ID: $PROJECT_ID"
echo "  WIF_PROVIDER: $PROVIDER_NAME"
echo "  WIF_SERVICE_ACCOUNT: $SERVICE_ACCOUNT_EMAIL"
echo ""
echo "GitHub Actions workflow configuration:"
echo "  - name: Authenticate to Google Cloud"
echo "    uses: google-github-actions/auth@v2"
echo "    with:"
echo "      workload_identity_provider: \${{ secrets.WIF_PROVIDER }}"
echo "      service_account: \${{ secrets.WIF_SERVICE_ACCOUNT }}"
echo ""
echo "Next steps:"
echo "1. Add the secrets above to your GitHub repository settings"
echo "2. Update your GitHub Actions workflows to use Workload Identity"
echo "3. Test the authentication in your CI/CD pipeline"

# Verify the setup
echo ""
echo "Verifying setup..."
if gcloud iam workload-identity-pools describe "$POOL_ID" --location="global" --format="value(name)" | grep -q "$POOL_ID"; then
    echo "✅ Workload Identity Pool created successfully"
else
    echo "❌ Workload Identity Pool creation failed"
    exit 1
fi

if gcloud iam workload-identity-pools providers describe "$PROVIDER_ID" \
    --workload-identity-pool="$POOL_ID" \
    --location="global" --format="value(name)" | grep -q "$PROVIDER_ID"; then
    echo "✅ Workload Identity Provider created successfully"
else
    echo "❌ Workload Identity Provider creation failed"
    exit 1
fi

if gcloud iam service-accounts describe "$SERVICE_ACCOUNT_EMAIL" --format="value(email)" | grep -q "$SERVICE_ACCOUNT_EMAIL"; then
    echo "✅ Service Account created successfully"
else
    echo "❌ Service Account creation failed"
    exit 1
fi

echo ""
echo "🎉 Workload Identity Federation is ready!"