# Quick Start Guide

## ✅ Good News!

All your required software is already installed:
- ✅ AWS CLI v2.17.25
- ✅ Pulumi v3.145.0
- ✅ Python 3.11.3
- ✅ Git 2.39.1
- ✅ Docker 27.4.0

## 🚀 What You Need to Do Now

### Step 1: Initialize Git Repository

Run these commands in your terminal:

```bash
cd /Users/divyadhara/git_repos/pulumi-provisioning

# Initialize git repository
git init

# Set default branch to 'main' (modern standard)
git branch -M main

# Create initial commit (after we add files)
# git add .
# git commit -m "Initial commit: AWS CI/CD with Pulumi project setup"
```

### Step 2: Verify AWS Configuration

```bash
# Check if AWS credentials are configured
aws sts get-caller-identity

# If this fails, configure AWS:
aws configure
# Enter your Access Key ID, Secret Access Key, region (us-east-1), and output format (json)
```

**If you don't have AWS credentials yet:**
1. Go to AWS Console → IAM → Users
2. Create a new user with programmatic access
3. Attach `AdministratorAccess` policy (for development)
4. Save the Access Key ID and Secret Access Key
5. Run `aws configure` with these credentials

### Step 3: Verify Pulumi Login

```bash
# Check if logged in to Pulumi
pulumi whoami

# If not logged in:
pulumi login
# Choose "Log in with browser" (easiest option)
```

**If you don't have a Pulumi account:**
1. Go to https://app.pulumi.com/
2. Sign up (use GitHub for easiest setup)
3. After signup, run `pulumi login`

### Step 4: Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `pulumi-provisioning` (or your choice)
3. Description: "AWS CI/CD pipeline with Pulumi, GitHub Actions, and FastAPI"
4. Choose Public or Private
5. **DO NOT** initialize with README, .gitignore, or license
6. Click "Create repository"

### Step 5: Connect Local Repo to GitHub

After creating the GitHub repo, run:

```bash
# Replace YOUR_USERNAME with your GitHub username
git remote add origin https://github.com/YOUR_USERNAME/pulumi-provisioning.git

# Or if you prefer SSH:
git remote add origin git@github.com:YOUR_USERNAME/pulumi-provisioning.git

# Verify remote was added
git remote -v
```

### Step 6: Run Verification Script

```bash
# Make script executable (if not already)
chmod +x verify-setup.sh

# Run verification
./verify-setup.sh
```

This will check:
- ✅ All software is installed
- ✅ AWS credentials are configured
- ✅ Pulumi is logged in
- ✅ Git repository is set up
- ✅ Project structure exists

## 📋 Setup Checklist

Before we start building, make sure:

- [ ] Git repository initialized (`git init`)
- [ ] AWS credentials configured (`aws configure`)
- [ ] AWS credentials verified (`aws sts get-caller-identity`)
- [ ] Pulumi account created (https://app.pulumi.com/)
- [ ] Pulumi logged in (`pulumi login`)
- [ ] GitHub repository created
- [ ] Git remote added (`git remote add origin ...`)
- [ ] Verification script passes (`./verify-setup.sh`)

## 🎯 What We Can Start Building

Once the checklist above is complete, we can immediately start building:

1. ✅ Project structure and all directories
2. ✅ Component-based Pulumi infrastructure code
3. ✅ FastAPI application
4. ✅ Docker configuration
5. ✅ GitHub Actions workflows
6. ✅ Nginx configuration
7. ✅ Documentation

## ⏳ What We'll Set Up Later

These can be configured after we have the code:

- AWS OIDC provider (for GitHub Actions)
- GitHub Secrets (PULUMI_ACCESS_TOKEN)
- Domain registration (Route53)
- First deployment

## 🆘 Need Help?

- **Detailed setup instructions:** See `SETUP.md`
- **Verification issues:** Run `./verify-setup.sh` to see what's missing
- **AWS setup help:** https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-quickstart.html
- **Pulumi setup help:** https://www.pulumi.com/docs/install/

## 🚦 Ready to Start?

Once you've completed the checklist above, let me know and we can start building the project! 

You can say:
- "I've completed the setup, let's start building"
- "I need help with [specific step]"
- "Let's proceed with the project"

