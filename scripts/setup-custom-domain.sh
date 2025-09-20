#!/bin/bash
# Setup custom domain and SSL certificate for Cloud Run services

set -e

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-your-project-id}"
REGION="${GCP_REGION:-us-central1}"
DOMAIN="${CUSTOM_DOMAIN:-todolist.yourdomain.com}"
BACKEND_SUBDOMAIN="${BACKEND_SUBDOMAIN:-api.todolist.yourdomain.com}"
FRONTEND_SUBDOMAIN="${FRONTEND_SUBDOMAIN:-todolist.yourdomain.com}"

echo "Setting up custom domain for TODO application"
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo "Frontend Domain: $FRONTEND_SUBDOMAIN"
echo "Backend Domain: $BACKEND_SUBDOMAIN"

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
    domains.googleapis.com \
    certificatemanager.googleapis.com \
    run.googleapis.com

# Function to create domain mapping
create_domain_mapping() {
    local service_name="$1"
    local domain="$2"

    echo "Creating domain mapping for $service_name -> $domain"

    # Check if domain mapping already exists
    if gcloud run domain-mappings describe --domain="$domain" --region="$REGION" &>/dev/null; then
        echo "  Domain mapping for $domain already exists"
        return 0
    fi

    # Create the domain mapping
    gcloud run domain-mappings create \
        --service="$service_name" \
        --domain="$domain" \
        --region="$REGION"

    echo "  ✅ Domain mapping created for $domain"
}

# Function to get DNS records that need to be configured
get_dns_records() {
    local domain="$1"

    echo "Getting DNS records for $domain..."

    # Get the domain mapping details
    local records=$(gcloud run domain-mappings describe --domain="$domain" --region="$REGION" --format="value(status.resourceRecords[].name,status.resourceRecords[].type,status.resourceRecords[].rrdata)")

    if [ -n "$records" ]; then
        echo "  DNS records needed for $domain:"
        echo "$records" | while read -r record; do
            echo "    $record"
        done
    else
        echo "  No DNS records found for $domain"
    fi
}

# Create SSL certificate
create_ssl_certificate() {
    local cert_name="todo-app-cert"
    local domains="$FRONTEND_SUBDOMAIN,$BACKEND_SUBDOMAIN"

    echo "Creating SSL certificate for domains: $domains"

    # Check if certificate already exists
    if gcloud certificate-manager certificates describe "$cert_name" --location="global" &>/dev/null; then
        echo "  SSL certificate $cert_name already exists"
        return 0
    fi

    # Create managed SSL certificate
    gcloud certificate-manager certificates create "$cert_name" \
        --location="global" \
        --domains="$domains"

    echo "  ✅ SSL certificate $cert_name created"
    echo "  Note: Certificate will be provisioned after DNS records are configured"
}

# Create Load Balancer (for HTTPS)
create_load_balancer() {
    echo "Creating Load Balancer for HTTPS termination..."

    # This is a simplified example. In production, you might want to use
    # a more sophisticated setup with Cloud Load Balancer
    echo "  For HTTPS termination, consider using:"
    echo "  1. Cloud Load Balancer with SSL certificates"
    echo "  2. Cloud CDN for global distribution"
    echo "  3. Cloud Armor for security"
    echo ""
    echo "  Alternatively, Cloud Run handles HTTPS automatically for custom domains"
}

# Main execution
echo "Starting domain setup..."

# Get current service URLs
BACKEND_URL=$(gcloud run services describe todo-backend --region="$REGION" --format="value(status.url)" 2>/dev/null || echo "")
FRONTEND_URL=$(gcloud run services describe todo-frontend --region="$REGION" --format="value(status.url)" 2>/dev/null || echo "")

if [ -z "$BACKEND_URL" ]; then
    echo "Warning: Backend service 'todo-backend' not found. Please deploy it first."
else
    echo "Backend service URL: $BACKEND_URL"
fi

if [ -z "$FRONTEND_URL" ]; then
    echo "Warning: Frontend service 'todo-frontend' not found. Please deploy it first."
else
    echo "Frontend service URL: $FRONTEND_URL"
fi

# Create domain mappings
if [ -n "$BACKEND_URL" ]; then
    create_domain_mapping "todo-backend" "$BACKEND_SUBDOMAIN"
fi

if [ -n "$FRONTEND_URL" ]; then
    create_domain_mapping "todo-frontend" "$FRONTEND_SUBDOMAIN"
fi

# Create SSL certificate
create_ssl_certificate

# Get DNS configuration instructions
echo ""
echo "📋 DNS Configuration Required"
echo "=============================="

if [ -n "$BACKEND_URL" ]; then
    get_dns_records "$BACKEND_SUBDOMAIN"
fi

if [ -n "$FRONTEND_URL" ]; then
    get_dns_records "$FRONTEND_SUBDOMAIN"
fi

# Instructions
echo ""
echo "🔧 Manual Steps Required"
echo "========================"
echo ""
echo "1. Configure DNS records:"
echo "   - Add the CNAME/A records shown above to your DNS provider"
echo "   - Wait for DNS propagation (can take up to 48 hours)"
echo ""
echo "2. Verify domain ownership:"
echo "   gcloud domains verify $DOMAIN"
echo ""
echo "3. Check certificate status:"
echo "   gcloud certificate-manager certificates describe todo-app-cert --location=global"
echo ""
echo "4. Test the domains:"
echo "   curl -I https://$FRONTEND_SUBDOMAIN"
echo "   curl -I https://$BACKEND_SUBDOMAIN/health"
echo ""
echo "5. Update environment variables:"
echo "   - Update NEXT_PUBLIC_API_URL to https://$BACKEND_SUBDOMAIN"
echo "   - Update CORS_ORIGINS to include https://$FRONTEND_SUBDOMAIN"
echo ""
echo "6. Redeploy services with updated configuration"

# Create a configuration file for reference
cat > domain-config.txt << EOF
# TODO App Domain Configuration
# Generated on: $(date)

Frontend Domain: https://$FRONTEND_SUBDOMAIN
Backend Domain: https://$BACKEND_SUBDOMAIN

# DNS Records (configure these with your DNS provider)
EOF

if [ -n "$BACKEND_URL" ]; then
    echo "# Backend DNS Records:" >> domain-config.txt
    gcloud run domain-mappings describe --domain="$BACKEND_SUBDOMAIN" --region="$REGION" --format="value(status.resourceRecords[].name,status.resourceRecords[].type,status.resourceRecords[].rrdata)" >> domain-config.txt 2>/dev/null || echo "# (Run after domain mapping is created)" >> domain-config.txt
fi

if [ -n "$FRONTEND_URL" ]; then
    echo "# Frontend DNS Records:" >> domain-config.txt
    gcloud run domain-mappings describe --domain="$FRONTEND_SUBDOMAIN" --region="$REGION" --format="value(status.resourceRecords[].name,status.resourceRecords[].type,status.resourceRecords[].rrdata)" >> domain-config.txt 2>/dev/null || echo "# (Run after domain mapping is created)" >> domain-config.txt
fi

echo ""
echo "✅ Domain setup completed!"
echo "📄 Configuration saved to: domain-config.txt"
echo ""
echo "Note: SSL certificates will be automatically provisioned once DNS records are configured"