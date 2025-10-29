#!/bin/bash

# =============================================================================
# SOCIALSYNC AI - ENTERPRISE REPO MIGRATION SCRIPT
# =============================================================================
# This script guides you through creating the enterprise repository
# with all commercial features (Stripe, billing, subscriptions)
# =============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Icons
CHECKMARK="✅"
CROSS="❌"
INFO="ℹ️"
ROCKET="🚀"

# =============================================================================
# FUNCTIONS
# =============================================================================

print_header() {
    echo ""
    echo -e "${BLUE}===============================================================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}===============================================================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}${CHECKMARK} $1${NC}"
}

print_error() {
    echo -e "${RED}${CROSS} $1${NC}"
}

print_info() {
    echo -e "${YELLOW}${INFO}  $1${NC}"
}

print_step() {
    echo ""
    echo -e "${BLUE}>>> $1${NC}"
    echo ""
}

confirm() {
    read -p "$1 (y/n): " -n 1 -r
    echo
    [[ $REPLY =~ ^[Yy]$ ]]
}

# =============================================================================
# PRE-FLIGHT CHECKS
# =============================================================================

print_header "ENTERPRISE REPO MIGRATION - PRE-FLIGHT CHECKS"

# Check if we're in the right directory
if [ ! -f "CLAUDE.md" ]; then
    print_error "This script must be run from the root of socialsync-ai repository"
    exit 1
fi

print_success "In correct directory"

# Check if git is installed
if ! command -v git &> /dev/null; then
    print_error "Git is not installed"
    exit 1
fi

print_success "Git installed"

# Check if gh CLI is installed (optional)
if command -v gh &> /dev/null; then
    print_success "GitHub CLI (gh) installed"
    GH_CLI_AVAILABLE=true
else
    print_info "GitHub CLI (gh) not installed - you'll need to create repo manually"
    GH_CLI_AVAILABLE=false
fi

# Check git status
if [ -n "$(git status --porcelain)" ]; then
    print_error "You have uncommitted changes. Please commit or stash them first."
    git status --short
    exit 1
fi

print_success "Git working directory clean"

# =============================================================================
# USER INPUTS
# =============================================================================

print_header "CONFIGURATION"

# Get GitHub username
read -p "Enter your GitHub username: " GITHUB_USERNAME
if [ -z "$GITHUB_USERNAME" ]; then
    print_error "GitHub username cannot be empty"
    exit 1
fi

# Get enterprise repo name
read -p "Enter enterprise repo name (default: socialsync-ai-enterprise): " ENTERPRISE_REPO_NAME
ENTERPRISE_REPO_NAME=${ENTERPRISE_REPO_NAME:-socialsync-ai-enterprise}

# Confirm details
echo ""
print_info "Configuration:"
echo "  GitHub Username: $GITHUB_USERNAME"
echo "  Enterprise Repo: $ENTERPRISE_REPO_NAME"
echo "  Repository URL: https://github.com/$GITHUB_USERNAME/$ENTERPRISE_REPO_NAME"
echo ""

if ! confirm "Is this correct?"; then
    print_error "Aborted by user"
    exit 1
fi

# =============================================================================
# CREATE ENTERPRISE REPO
# =============================================================================

print_header "CREATING ENTERPRISE REPOSITORY"

if [ "$GH_CLI_AVAILABLE" = true ]; then
    print_step "Creating private repository using GitHub CLI..."

    if gh repo create "$ENTERPRISE_REPO_NAME" --private --description "SocialSync AI - Enterprise SaaS Edition"; then
        print_success "Repository created: $GITHUB_USERNAME/$ENTERPRISE_REPO_NAME"
    else
        print_error "Failed to create repository"
        exit 1
    fi
else
    print_info "Please create the repository manually:"
    echo "  1. Go to: https://github.com/new"
    echo "  2. Repository name: $ENTERPRISE_REPO_NAME"
    echo "  3. Visibility: Private"
    echo "  4. Do NOT initialize with README, .gitignore, or license"
    echo ""

    if ! confirm "Have you created the repository?"; then
        print_error "Please create the repository first"
        exit 1
    fi
fi

# =============================================================================
# PREPARE MIGRATION DIRECTORY
# =============================================================================

print_header "PREPARING MIGRATION"

MIGRATION_DIR="$(dirname "$(pwd)")/${ENTERPRISE_REPO_NAME}"

if [ -d "$MIGRATION_DIR" ]; then
    print_error "Directory $MIGRATION_DIR already exists"

    if confirm "Remove and recreate?"; then
        rm -rf "$MIGRATION_DIR"
        print_success "Removed existing directory"
    else
        exit 1
    fi
fi

print_step "Creating migration directory..."
mkdir -p "$MIGRATION_DIR"
print_success "Created $MIGRATION_DIR"

# =============================================================================
# COPY CODE WITH FRESH GIT HISTORY
# =============================================================================

print_header "COPYING CODE TO ENTERPRISE REPO"

print_step "Copying all files (excluding .git)..."
rsync -av --exclude='.git' --exclude='node_modules' --exclude='.next' --exclude='__pycache__' ./ "$MIGRATION_DIR/"
print_success "Files copied"

# =============================================================================
# APPLY ENTERPRISE CUSTOMIZATIONS
# =============================================================================

print_header "APPLYING ENTERPRISE CUSTOMIZATIONS"

print_step "Replacing README.md with enterprise version..."
cp .enterprise_setup/README_ENTERPRISE.md "$MIGRATION_DIR/README.md"
# Replace placeholder
sed -i "s/YOUR_USERNAME/$GITHUB_USERNAME/g" "$MIGRATION_DIR/README.md"
print_success "README.md updated"

print_step "Adding DEPLOYMENT.md..."
cp .enterprise_setup/DEPLOYMENT.md "$MIGRATION_DIR/DEPLOYMENT.md"
print_success "DEPLOYMENT.md added"

print_step "Adding proprietary LICENSE..."
cp .enterprise_setup/LICENSE "$MIGRATION_DIR/LICENSE"
print_success "LICENSE added"

# =============================================================================
# INITIALIZE GIT REPO
# =============================================================================

print_header "INITIALIZING GIT REPOSITORY"

cd "$MIGRATION_DIR"

print_step "Creating fresh git repository..."
git init
git branch -M main
print_success "Git initialized"

print_step "Staging all files..."
git add .
print_success "Files staged"

print_step "Creating initial commit..."
git commit -m "Initial commit - Enterprise Edition

🔐 Commercial SaaS version with:
- Stripe integration (payments & subscriptions)
- Google Auth + Supabase authentication
- Credit system with usage limits
- Billing & pricing pages
- Subscription management
- Advanced analytics
- AI-powered automation

📦 Features:
- WhatsApp & Instagram integration
- Content scheduling & calendar
- Automated comment responses
- AI Studio for content creation
- Knowledge base with RAG
- Topic modeling & analytics

🏗️ Tech Stack:
- Frontend: Next.js 14, TypeScript, Tailwind
- Backend: FastAPI, Python 3.12, Celery
- Database: Supabase (PostgreSQL + pgvector)
- AI: LangChain, OpenRouter, Gemini
- Infrastructure: Docker, Redis, Stripe

For open-source version: https://github.com/$GITHUB_USERNAME/socialsync-ai

© 2025 SocialSync AI. All Rights Reserved."

print_success "Initial commit created"

# =============================================================================
# PUSH TO GITHUB
# =============================================================================

print_header "PUSHING TO GITHUB"

print_step "Adding remote origin..."
git remote add origin "https://github.com/$GITHUB_USERNAME/$ENTERPRISE_REPO_NAME.git"
print_success "Remote added"

print_step "Pushing to main branch..."
if git push -u origin main; then
    print_success "Code pushed to GitHub"
else
    print_error "Failed to push to GitHub"
    print_info "You may need to authenticate. Try:"
    echo "  cd $MIGRATION_DIR"
    echo "  git push -u origin main"
    exit 1
fi

# =============================================================================
# POST-MIGRATION STEPS
# =============================================================================

print_header "MIGRATION COMPLETE! ${ROCKET}"

print_success "Enterprise repository created and pushed"

echo ""
echo -e "${GREEN}${ROCKET} Repository URL:${NC}"
echo "  https://github.com/$GITHUB_USERNAME/$ENTERPRISE_REPO_NAME"
echo ""

print_info "Next steps:"
echo ""
echo "  1. Configure repository settings:"
echo "     https://github.com/$GITHUB_USERNAME/$ENTERPRISE_REPO_NAME/settings"
echo ""
echo "     ${CHECKMARK} Branch protection rules"
echo "     ${CHECKMARK} Add collaborators"
echo "     ${CHECKMARK} Setup GitHub Secrets for CI/CD"
echo ""
echo "  2. Review and update documentation:"
echo "     - README.md (check links and details)"
echo "     - DEPLOYMENT.md (update with your infrastructure)"
echo "     - .env.example (verify all variables)"
echo ""
echo "  3. Setup GitHub Secrets:"
echo "     ${INFO}  SUPABASE_URL_PROD"
echo "     ${INFO}  SUPABASE_SERVICE_KEY_PROD"
echo "     ${INFO}  STRIPE_SECRET_KEY_LIVE"
echo "     ${INFO}  STRIPE_WEBHOOK_SECRET"
echo "     ${INFO}  (see DEPLOYMENT.md for complete list)"
echo ""
echo "  4. Test the deployment:"
echo "     cd $MIGRATION_DIR"
echo "     docker-compose up -d"
echo ""

print_info "Enterprise repo location: $MIGRATION_DIR"

# =============================================================================
# OFFER TO CLEAN CURRENT REPO FOR OPEN-SOURCE
# =============================================================================

echo ""
echo -e "${BLUE}===============================================================================${NC}"
echo ""

if confirm "Do you want to proceed with cleaning the current repo for open-source?"; then
    print_info "You can now run the open-source conversion script"
    print_info "This will remove Stripe, change auth, and add AGPL license"
    echo ""
    print_info "Next: Run the open-source conversion from the original repo"
else
    print_success "Migration complete!"
    print_info "The current repo is unchanged and contains all commercial features"
    print_info "You can clean it for open-source later"
fi

echo ""
print_header "ALL DONE! ${ROCKET}${ROCKET}${ROCKET}"
echo ""
