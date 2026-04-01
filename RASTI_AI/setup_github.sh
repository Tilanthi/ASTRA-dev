#!/bin/bash
# Script to create and push ASTRA repository to GitHub

# Configuration
REPO_NAME="ASTRA"
DESCRIPTION="ASTRA: Autonomous System for Scientific Discovery in Astrophysics - An AGI-inspired framework for autonomous hypothesis generation and validation"
PROJECT_ROOT="/Users/gjw255/astrodata/SWARM/STAN_XI_ASTRO"

echo "=== ASTRA GitHub Repository Setup ==="
echo ""
echo "This script will:"
echo "1. Initialize git repository"
echo "2. Create a .gitignore file"
echo "3. Create initial commit"
echo "4. Guide you to create GitHub repository"
echo "5. Push to GitHub"
echo ""

# Navigate to project root
cd "$PROJECT_ROOT" || exit 1

# Check if .git exists
if [ -d ".git" ]; then
    echo "Git repository already initialized"
else
    echo "Initializing git repository..."
    git init
fi

# Create .gitignore if it doesn't exist
if [ ! -f ".gitignore" ]; then
    echo "Creating .gitignore file..."
    cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual Environment
venv/
ENV/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Jupyter
.ipynb_checkpoints/
*.ipynb

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/

# Data and models (large files)
*.csv
*.h5
*.hdf5
*.pkl
*.pickle
data/
models/

# Logs
*.log

# OS
.DS_Store
Thumbs.db

# ASTRA specific
.claude/
*.backup
*.bak

# Persistent memory (may contain sensitive data)
.stan_persistent/

# Environment variables
.env
.env.local
EOF
fi

# Check if there are any commits
if git rev-parse HEAD > /dev/null 2>&1; then
    echo "Repository already has commits"
else
    echo "Creating initial commit..."
    git add .
    git commit -m "Initial commit: ASTRA v4.7 - Autonomous System for Scientific Discovery in Astrophysics"
fi

echo ""
echo "=== Next Steps ==="
echo ""
echo "1. Create a new repository on GitHub:"
echo "   - Go to: https://github.com/new"
echo "   - Repository name: ASTRA"
echo "   - Description: $DESCRIPTION"
echo "   - Set to PUBLIC"
echo "   - DO NOT initialize with README"
echo ""
echo "2. After creating the repository, run:"
echo ""
echo "   cd $PROJECT_ROOT"
echo "   git remote add origin https://github.com/YOUR_USERNAME/ASTRA.git"
echo "   git branch -M main"
echo "   git push -u origin main"
echo ""
echo "Replace YOUR_USERNAME with your actual GitHub username."
echo ""
echo "Your actual GitHub username is NOT your email - it's the username you use to log in."
echo ""
