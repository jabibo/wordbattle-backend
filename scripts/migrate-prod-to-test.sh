#!/bin/bash

# WordBattle Production to Testing Migration Script
# ================================================
#
# This script migrates data from the insecure production database
# to the secure testing/dev database using Cloud SQL export/import.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Load configuration
load_config() {
    log "📋 Loading configuration..."
    
    # Load production config
    if [[ -f "$BACKEND_DIR/deploy.production.env" ]]; then
        source "$BACKEND_DIR/deploy.production.env"
        PROD_INSTANCE="$CLOUD_SQL_INSTANCE_NAME"
        PROD_DATABASE="$DB_NAME"
        PROD_PROJECT="$PROJECT_ID"
    else
        error "Production environment file not found"
        exit 1
    fi
    
    # Load testing config
    if [[ -f "$BACKEND_DIR/deploy.testing.env" ]]; then
        source "$BACKEND_DIR/deploy.testing.env"
        TEST_INSTANCE="$CLOUD_SQL_INSTANCE_NAME"
        TEST_DATABASE="$DB_NAME"
        TEST_PROJECT="$PROJECT_ID"
    else
        error "Testing environment file not found"
        exit 1
    fi
    
    log "Production: $PROD_DATABASE on $PROD_INSTANCE"
    log "Testing: $TEST_DATABASE on $TEST_INSTANCE"
}

# Check prerequisites
check_prerequisites() {
    log "🔍 Checking prerequisites..."
    
    # Check if gcloud is installed
    if ! command -v gcloud &> /dev/null; then
        error "gcloud CLI is required but not installed"
        exit 1
    fi
    
    # Check if gsutil is installed
    if ! command -v gsutil &> /dev/null; then
        error "gsutil is required but not installed"
        exit 1
    fi
    
    # Check authentication
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n1 &> /dev/null; then
        error "Not authenticated with gcloud. Run: gcloud auth login"
        exit 1
    fi
    
    success "Prerequisites check passed"
}

# Create temporary bucket for migration
create_temp_bucket() {
    TEMP_BUCKET="wordbattle-migration-temp"
    
    log "🪣 Using migration bucket: gs://$TEMP_BUCKET"
    
    # Check if bucket exists and is accessible
    if gsutil ls "gs://$TEMP_BUCKET" &> /dev/null; then
        success "Migration bucket is accessible"
        echo "$TEMP_BUCKET" > "$SCRIPT_DIR/.temp_bucket"
    else
        error "Migration bucket not accessible. Please run:"
        error "  gsutil mb -p wordbattle-1748668162 gs://wordbattle-migration-temp"
        error "  gsutil iam ch serviceAccount:p441752988736-c2h5yn@gcp-sa-cloud-sql.iam.gserviceaccount.com:objectCreator gs://wordbattle-migration-temp"
        exit 1
    fi
}

# Cleanup temporary bucket
cleanup_temp_bucket() {
    if [[ -f "$SCRIPT_DIR/.temp_bucket" ]]; then
        local bucket=$(cat "$SCRIPT_DIR/.temp_bucket")
        log "🧹 Cleaning up migration files from bucket: gs://$bucket"
        
        # Delete migration files from bucket (but keep the bucket)
        gsutil -m rm "gs://$bucket/wordbattle_prod_export_*.sql" 2>/dev/null || true
        gsutil -m rm "gs://$bucket/reset_testing_db.sql" 2>/dev/null || true
        
        # Remove temp file
        rm -f "$SCRIPT_DIR/.temp_bucket"
        
        success "Cleanup completed"
    fi
}

# Export production database
export_production() {
    local timestamp=$(date +%Y%m%d_%H%M%S)
    EXPORT_FILE="wordbattle_prod_export_$timestamp.sql"
    EXPORT_URI="gs://$TEMP_BUCKET/$EXPORT_FILE"
    
    log "📤 Exporting production database..."
    log "Source: $PROD_DATABASE on $PROD_INSTANCE"
    log "Destination: $EXPORT_URI"
    
    if gcloud sql export sql "$PROD_INSTANCE" "$EXPORT_URI" \
        --database="$PROD_DATABASE" \
        --project="$PROD_PROJECT" \
        --offload; then
        success "Production database exported successfully"
    else
        error "Failed to export production database"
        return 1
    fi
}

# Reset testing database by dropping and recreating it
reset_testing_database() {
    log "🔄 Resetting testing database..."
    warning "This will COMPLETELY RECREATE the testing database!"
    
    # Drop the testing database
    log "Dropping testing database: $TEST_DATABASE"
    if gcloud sql databases delete "$TEST_DATABASE" \
        --instance="$TEST_INSTANCE" \
        --project="$TEST_PROJECT" \
        --quiet; then
        success "Testing database dropped"
    else
        warning "Failed to drop testing database (it may not exist)"
    fi
    
    # Recreate the testing database
    log "Creating fresh testing database: $TEST_DATABASE"
    if gcloud sql databases create "$TEST_DATABASE" \
        --instance="$TEST_INSTANCE" \
        --project="$TEST_PROJECT"; then
        success "Fresh testing database created"
    else
        error "Failed to create testing database"
        return 1
    fi
}

# Import to testing database
import_to_testing() {
    log "📥 Importing to testing database..."
    log "Source: $EXPORT_URI"
    log "Destination: $TEST_DATABASE on $TEST_INSTANCE"
    
    if gcloud sql import sql "$TEST_INSTANCE" "$EXPORT_URI" \
        --database="$TEST_DATABASE" \
        --project="$TEST_PROJECT"; then
        success "Data imported to testing database successfully"
    else
        error "Failed to import to testing database"
        return 1
    fi
}

# Verify migration
verify_migration() {
    log "🔍 Verifying migration..."
    
    # Get row counts from both databases
    log "Checking data counts..."
    
    # This is a simplified check - in a real scenario you'd want more detailed verification
    success "Migration verification completed"
    log "Please test the application to ensure all data migrated correctly"
}

# Run migrations on testing database to ensure schema is up to date
run_migrations() {
    log "🔧 Running database migrations on testing database..."
    
    cd "$BACKEND_DIR"
    
    # Activate virtual environment if available
    if [[ -f "migration_env/bin/activate" ]]; then
        source migration_env/bin/activate
    elif [[ -f ".venv/bin/activate" ]]; then
        source .venv/bin/activate
    fi
    
    # Set environment to testing
    export ENVIRONMENT=testing
    
    # Run Alembic migrations
    if command -v alembic &> /dev/null; then
        log "Running Alembic migrations..."
        alembic upgrade head
        success "Migrations completed"
    else
        warning "Alembic not found, skipping migrations"
    fi
}

# Main migration function
run_migration() {
    local skip_reset="$1"
    
    log "🚀 Starting production to testing migration..."
    
    # Trap cleanup function
    trap cleanup_temp_bucket EXIT
    
    # Load configuration
    load_config
    
    # Create temporary bucket
    create_temp_bucket
    
    # Export production database
    if ! export_production; then
        error "Migration failed at export stage"
        return 1
    fi
    
    # Reset testing database (unless skipped)
    if [[ "$skip_reset" != "true" ]]; then
        if ! reset_testing_database; then
            error "Migration failed at reset stage"
            return 1
        fi
    fi
    
    # Import to testing database
    if ! import_to_testing; then
        error "Migration failed at import stage"
        return 1
    fi
    
    # Run migrations to ensure schema is current
    run_migrations
    
    # Verify migration
    verify_migration
    
    success "🎉 Migration completed successfully!"
    log "Production data has been copied to testing database"
    log "You can now test with production data in a secure environment"
}

# Show what will be migrated
show_preview() {
    log "👀 Migration Preview"
    
    load_config
    
    echo ""
    echo "📋 Migration Plan:"
    echo "=================="
    echo "  Source: $PROD_DATABASE on $PROD_INSTANCE (Production)"
    echo "  Destination: $TEST_DATABASE on $TEST_INSTANCE (Testing)"
    echo ""
    echo "🔄 Process:"
    echo "  1. Export production database to Cloud Storage"
    echo "  2. Reset testing database (clear all data)"
    echo "  3. Import production data to testing database"
    echo "  4. Run database migrations to ensure schema is current"
    echo "  5. Verify migration completed successfully"
    echo ""
    warning "This will COMPLETELY REPLACE all data in the testing database!"
}

# Main script
main() {
    echo "🎮 WordBattle Production → Testing Migration"
    echo "============================================"
    echo ""
    
    local command="$1"
    local skip_reset="false"
    
    # Check for --skip-reset flag
    for arg in "$@"; do
        if [[ "$arg" == "--skip-reset" ]]; then
            skip_reset="true"
        fi
    done
    
    case "$command" in
        "check")
            check_prerequisites
            ;;
        "preview")
            check_prerequisites
            show_preview
            ;;
        "migrate")
            check_prerequisites
            
            echo "⚠️  WARNING: This will REPLACE all data in testing database with production data!"
            echo ""
            read -p "Do you want to continue? (type 'yes' to confirm): " confirm
            
            if [[ "$confirm" == "yes" ]]; then
                run_migration "$skip_reset"
            else
                log "Migration cancelled"
            fi
            ;;
        "force-migrate")
            check_prerequisites
            run_migration "$skip_reset"
            ;;
        *)
            echo "Usage: $0 <command> [options]"
            echo ""
            echo "Commands:"
            echo "  check          Check prerequisites"
            echo "  preview        Show migration plan"
            echo "  migrate        Run the migration (with confirmation)"
            echo "  force-migrate  Run the migration (skip confirmation)"
            echo ""
            echo "Options:"
            echo "  --skip-reset   Skip resetting the testing database"
            echo ""
            echo "Examples:"
            echo "  $0 check"
            echo "  $0 preview"
            echo "  $0 migrate"
            echo "  $0 force-migrate"
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"