#!/bin/bash
# Docker Helper Script for YOLOv8 Parking Detection System

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Print colored messages
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${GREEN}ℹ $1${NC}"
}

# Check if .env file exists
check_env_file() {
    if [ ! -f .env ]; then
        print_warning ".env file not found!"
        echo "Creating .env from .env.example..."
        cp .env.example .env
        print_info "Please edit .env file with your configuration"
        exit 1
    fi
}

# Development environment
dev_start() {
    print_info "Starting development environment..."
    check_env_file
    docker compose -f docker-compose.dev.yml up -d
    print_success "Development environment started!"
    echo ""
    print_info "Services available at:"
    echo "  - Application: http://localhost:5001"
    echo "  - MongoDB: mongodb://localhost:27017"
    echo "  - Mongo Express: http://localhost:8081 (admin/admin123)"
    echo ""
    echo "To view logs: ./docker-helper.sh dev-logs"
}

dev_stop() {
    print_info "Stopping development environment..."
    docker compose -f docker-compose.dev.yml down
    print_success "Development environment stopped!"
}

dev_restart() {
    print_info "Restarting development environment..."
    docker compose -f docker-compose.dev.yml restart
    print_success "Development environment restarted!"
}

dev_logs() {
    docker compose -f docker-compose.dev.yml logs -f
}

dev_shell() {
    docker compose -f docker-compose.dev.yml exec app /bin/bash
}

# Production environment
prod_start() {
    print_info "Starting production environment..."
    check_env_file
    
    # Check if gcs-credentials.json exists
    if [ ! -f gcs-credentials.json ]; then
        print_warning "gcs-credentials.json not found. GCS storage will be disabled."
    fi
    
    docker compose -f docker-compose.prod.yml up -d
    print_success "Production environment started!"
    echo ""
    print_info "Services available at:"
    echo "  - Application: http://localhost:80"
    echo "  - MongoDB: mongodb://localhost:27017"
    echo ""
    echo "To view logs: ./docker-helper.sh prod-logs"
}

prod_stop() {
    print_info "Stopping production environment..."
    docker compose -f docker-compose.prod.yml down
    print_success "Production environment stopped!"
}

prod_restart() {
    print_info "Restarting production environment..."
    docker compose -f docker-compose.prod.yml restart
    print_success "Production environment restarted!"
}

prod_logs() {
    docker compose -f docker-compose.prod.yml logs -f
}

prod_shell() {
    docker compose -f docker-compose.prod.yml exec app /bin/bash
}

# Build commands
build_dev() {
    print_info "Building development image..."
    docker compose -f docker-compose.dev.yml build
    print_success "Development image built!"
}

build_prod() {
    print_info "Building production image..."
    docker compose -f docker-compose.prod.yml build
    print_success "Production image built!"
}

# Cleanup commands
clean() {
    print_warning "This will remove all containers, volumes, and images. Are you sure? (y/N)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        print_info "Cleaning up..."
        docker compose -f docker-compose.dev.yml down -v
        docker compose -f docker-compose.prod.yml down -v
        docker compose down -v
        print_success "Cleanup complete!"
    else
        print_info "Cleanup cancelled"
    fi
}

# Database commands
db_backup() {
    print_info "Creating database backup..."
    BACKUP_FILE="mongodb-backup/backup_$(date +%Y%m%d_%H%M%S).gz"
    docker compose -f docker-compose.prod.yml exec -T mongodb \
        mongodump --archive --gzip | cat > "$BACKUP_FILE"
    print_success "Database backup created: $BACKUP_FILE"
}

db_restore() {
    if [ -z "$1" ]; then
        print_error "Usage: ./docker-helper.sh db-restore <backup_file>"
        exit 1
    fi
    
    if [ ! -f "$1" ]; then
        print_error "Backup file not found: $1"
        exit 1
    fi
    
    print_info "Restoring database from: $1"
    cat "$1" | docker compose -f docker-compose.prod.yml exec -T mongodb \
        mongorestore --archive --gzip
    print_success "Database restored!"
}

# Status commands
status() {
    echo "=== Docker Containers Status ==="
    docker compose -f docker-compose.dev.yml ps
    echo ""
    docker compose -f docker-compose.prod.yml ps
}

# Help message
show_help() {
    cat << EOF
YOLOv8 Parking Detection System - Docker Helper Script

Usage: ./docker-helper.sh [command]

Development Commands:
  dev-start       Start development environment (port 5001)
  dev-stop        Stop development environment
  dev-restart     Restart development environment
  dev-logs        Show development logs (follow)
  dev-shell       Open shell in development container
  build-dev       Build development image

Production Commands:
  prod-start      Start production environment (port 80)
  prod-stop       Stop production environment
  prod-restart    Restart production environment
  prod-logs       Show production logs (follow)
  prod-shell      Open shell in production container
  build-prod      Build production image

Database Commands:
  db-backup       Create MongoDB backup
  db-restore      Restore MongoDB from backup file

Utility Commands:
  status          Show status of all containers
  clean           Remove all containers, volumes, and images
  help            Show this help message

Examples:
  ./docker-helper.sh dev-start        # Start development
  ./docker-helper.sh prod-start       # Start production
  ./docker-helper.sh dev-logs         # View development logs
  ./docker-helper.sh db-backup        # Backup database
  ./docker-helper.sh clean            # Clean everything

EOF
}

# Main script logic
case "$1" in
    # Development
    dev-start)
        dev_start
        ;;
    dev-stop)
        dev_stop
        ;;
    dev-restart)
        dev_restart
        ;;
    dev-logs)
        dev_logs
        ;;
    dev-shell)
        dev_shell
        ;;
    build-dev)
        build_dev
        ;;
    
    # Production
    prod-start)
        prod_start
        ;;
    prod-stop)
        prod_stop
        ;;
    prod-restart)
        prod_restart
        ;;
    prod-logs)
        prod_logs
        ;;
    prod-shell)
        prod_shell
        ;;
    build-prod)
        build_prod
        ;;
    
    # Database
    db-backup)
        db_backup
        ;;
    db-restore)
        db_restore "$2"
        ;;
    
    # Utility
    status)
        status
        ;;
    clean)
        clean
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
