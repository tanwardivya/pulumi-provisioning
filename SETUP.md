# Pre-Project Setup Guide

This guide walks you through all the prerequisites and setup needed before we start building the project.

## Prerequisites Checklist

### 1. Required Software Installation

#### AWS CLI
```bash
# Check if AWS CLI is installed
aws --version

# If not installed, install via Homebrew (macOS)
brew install awscli

# Or download from: https://aws.amazon.com/cli/
```

#### Pulumi CLI
```bash
# Check if Pulumi is installed
pulumi version

# If not installed, install via Homebrew (macOS)
brew install pulumi

# Or use install script:
curl -fsSL https://get.pulumi.com | sh

# Or download from: https://www.pulumi.com/docs/install/
```

#### Python 3.11+
```bash
# Check Python version
python3 --version

# Should be 3.11 or higher. If not, install via Homebrew:
brew install python@3.11

# Or download from: https://www.python.org/downloads/
```

#### Git
```bash
# Check if Git is installed
git --version

# If not installed, install via Homebrew:
brew install git
```

#### Docker (for local testing)
```bash
# Check if Docker is installed
docker --version

# If not installed, download from: https://www.docker.com/products/docker-desktop
```

---

## Step-by-Step Setup Instructions

### Step 1: AWS Account Setup

1. **Create AWS Account** (if you don't have one)
   - Go to https://aws.amazon.com/
   - Sign up for a free tier account (12 months free tier available)

2. **Create IAM User for Local Development**
   - Go to AWS Console → IAM → Users
   - Click "Create user"
   - Username: `pulumi-dev-user` (or your choice)
   - Enable "Access key - Programmatic access"
   - Attach policies:
     - `AdministratorAccess` (for development - restrict in production)
     - Or create custom policy with: EC2, S3, RDS, IAM, Route53, ACM, VPC permissions
   - **Save the Access Key ID and Secret Access Key** (you'll need these)

3. **Configure AWS CLI Locally**
   ```bash
   aws configure
   ```
   - Enter your Access Key ID
   - Enter your Secret Access Key
   - Default region: `us-east-1` (or your preferred region)
   - Default output format: `json`

4. **Verify AWS Configuration**
   ```bash
   aws sts get-caller-identity
   ```
   - Should return your AWS account ID and user ARN

---

### Step 2: Pulumi Cloud Setup

1. **Create Pulumi Cloud Account**
   - Go to https://app.pulumi.com/
   - Sign up with GitHub (recommended) or email

2. **Get Pulumi Access Token**
   - After login, go to: https://app.pulumi.com/account/tokens
   - Click "Create token"
   - Name: `local-dev-token` (or your choice)
   - **Copy and save the token** (you'll need this for GitHub Actions later)

3. **Login to Pulumi CLI**
   ```bash
   pulumi login
   ```
   - Choose "Log in with browser" (recommended)
   - Or use access token: `pulumi login --save-url https://api.pulumi.com`

4. **Verify Pulumi Login**
   ```bash
   pulumi whoami
   ```
   - Should show your Pulumi username

---

### Step 3: GitHub Repository Setup

1. **Initialize Git Repository** (in project folder)
   ```bash
   cd /Users/divyadhara/git_repos/pulumi-provisioning
   git init
   ```

2. **Create GitHub Repository**
   - Go to https://github.com/new
   - Repository name: `pulumi-provisioning` (or your choice)
   - Description: "AWS CI/CD pipeline with Pulumi, GitHub Actions, and FastAPI"
   - Choose Public or Private
   - **DO NOT** initialize with README, .gitignore, or license (we'll create these)
   - Click "Create repository"

3. **Connect Local Repo to GitHub**
   ```bash
   # Add remote (replace YOUR_USERNAME with your GitHub username)
   git remote add origin https://github.com/YOUR_USERNAME/pulumi-provisioning.git
   
   # Or if using SSH:
   git remote add origin git@github.com:YOUR_USERNAME/pulumi-provisioning.git
   ```

4. **Verify Remote**
   ```bash
   git remote -v
   ```

---

### Step 4: GitHub Secrets Setup (for CI/CD)

**Note:** We'll set these up after we create the GitHub Actions workflows, but here's what you'll need:

1. **Go to GitHub Repository Settings**
   - Navigate to: Settings → Secrets and variables → Actions

2. **Add Required Secrets:**
   - `PULUMI_ACCESS_TOKEN` - Your Pulumi access token from Step 2

3. **AWS OIDC Setup** (we'll do this after creating infrastructure)
   - This requires creating an IAM role in AWS
   - We'll set this up when we create the GitHub Actions workflow

---

### Step 5: AWS OIDC Provider Setup (One-time)

**Note:** This is required for GitHub Actions to work. See **[OIDC_SETUP.md](OIDC_SETUP.md)** for a complete beginner-friendly guide.

**Quick Summary:**
1. Create OIDC Identity Provider in AWS IAM
2. Create IAM Role with trust policy for GitHub
3. Add Role ARN to GitHub Secrets

**For detailed instructions with screenshots and troubleshooting, see: [OIDC_SETUP.md](OIDC_SETUP.md)**

---

## Quick Setup Commands

Run these commands to verify everything is set up:

```bash
# Check all prerequisites
echo "=== Checking Prerequisites ==="
echo "AWS CLI:"
aws --version
echo "\nPulumi:"
pulumi version
echo "\nPython:"
python3 --version
echo "\nGit:"
git --version
echo "\nDocker:"
docker --version

# Verify AWS credentials
echo "\n=== AWS Credentials ==="
aws sts get-caller-identity

# Verify Pulumi login
echo "\n=== Pulumi Login ==="
pulumi whoami

# Check Git remote
echo "\n=== Git Remote ==="
git remote -v
```

---

## What We Can Start Building Now

✅ **Can start immediately:**
- Project structure and files
- Pulumi components and infrastructure code
- FastAPI application code
- Docker configuration
- GitHub Actions workflow files
- Documentation

⏳ **Need to wait for:**
- AWS OIDC setup (can be done manually or via Pulumi)
- GitHub Secrets (after workflow files are created)
- Domain registration (can be done later)
- First deployment (after all setup is complete)

---

## Recommended Order

1. **Do Now:**
   - Install all required software (AWS CLI, Pulumi, Python, Git, Docker)
   - Set up AWS account and configure AWS CLI
   - Set up Pulumi Cloud account and login
   - Initialize Git repo and connect to GitHub

2. **We Can Build:**
   - All project code and structure
   - Infrastructure components
   - Application code
   - CI/CD workflows

3. **Before First Deployment:**
   - Add PULUMI_ACCESS_TOKEN to GitHub Secrets
   - Set up AWS OIDC provider and IAM role
   - Register domain (if using Route53)

---

## Next Steps

Once you've completed the setup above, we can:
1. Initialize the project structure
2. Create all the component-based Pulumi infrastructure
3. Build the FastAPI application
4. Set up GitHub Actions workflows
5. Configure AWS OIDC for secure deployments

Let me know when you're ready to proceed!

