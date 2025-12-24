#!/bin/bash

# Setup Verification Script
# Run this script to verify all prerequisites are installed and configured

echo "=========================================="
echo "  Setup Verification Script"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_command() {
    if command -v $1 &> /dev/null; then
        echo -e "${GREEN}✓${NC} $1 is installed: $(command -v $1)"
        return 0
    else
        echo -e "${RED}✗${NC} $1 is NOT installed"
        return 1
    fi
}

check_version() {
    if command -v $1 &> /dev/null; then
        version=$($1 $2 2>&1 | head -n 1)
        echo -e "  Version: ${version}"
    fi
}

echo "1. Checking Required Software:"
echo "-------------------------------"
check_command "aws" && check_version "aws" "--version"
check_command "pulumi" && check_version "pulumi" "version"
check_command "python3" && check_version "python3" "--version"
check_command "git" && check_version "git" "--version"
check_command "docker" && check_version "docker" "--version"
echo ""

echo "2. Checking AWS Configuration:"
echo "-------------------------------"
if aws sts get-caller-identity &> /dev/null; then
    echo -e "${GREEN}✓${NC} AWS credentials are configured"
    aws sts get-caller-identity | grep -E "(Account|Arn|UserId)" | sed 's/^/  /'
else
    echo -e "${RED}✗${NC} AWS credentials are NOT configured"
    echo "  Run: aws configure"
fi
echo ""

echo "3. Checking Pulumi Login:"
echo "-------------------------"
if pulumi whoami &> /dev/null; then
    echo -e "${GREEN}✓${NC} Pulumi is logged in"
    echo "  User: $(pulumi whoami)"
else
    echo -e "${RED}✗${NC} Pulumi is NOT logged in"
    echo "  Run: pulumi login"
fi
echo ""

echo "4. Checking Git Repository:"
echo "----------------------------"
if [ -d .git ]; then
    echo -e "${GREEN}✓${NC} Git repository is initialized"
    if git remote -v &> /dev/null && [ ! -z "$(git remote -v)" ]; then
        echo -e "${GREEN}✓${NC} Git remote is configured:"
        git remote -v | sed 's/^/  /'
    else
        echo -e "${YELLOW}⚠${NC} Git remote is NOT configured"
        echo "  Run: git remote add origin <your-github-repo-url>"
    fi
else
    echo -e "${RED}✗${NC} Git repository is NOT initialized"
    echo "  Run: git init"
fi
echo ""

echo "5. Checking Project Structure:"
echo "-------------------------------"
required_dirs=("app" "infrastructure" ".github/workflows" "nginx" "scripts")
for dir in "${required_dirs[@]}"; do
    if [ -d "$dir" ]; then
        echo -e "${GREEN}✓${NC} $dir/ exists"
    else
        echo -e "${YELLOW}⚠${NC} $dir/ does not exist (will be created)"
    fi
done
echo ""

echo "=========================================="
echo "  Summary"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Complete AWS setup (if not done): aws configure"
echo "2. Complete Pulumi setup (if not done): pulumi login"
echo "3. Create GitHub repository and add remote"
echo "4. Review SETUP.md for detailed instructions"
echo ""
echo "Once all checks pass, you're ready to start building!"
echo ""

