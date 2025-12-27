# Deployment Strategy: Local vs GitHub Actions

## Recommendation: Use GitHub Actions for Deployments

### Why GitHub Actions is Better

1. **Security**: Uses OIDC (no long-lived credentials)
2. **Reproducible**: Same process every time
3. **Auditable**: All deployments tracked in git history
4. **Team-friendly**: Anyone can trigger deployments
5. **Automated**: Deploys on push/PR automatically
6. **Production-ready**: Industry standard approach

### When to Use Local Deployment

**Use local deployment ONLY for:**
- ✅ Initial testing and debugging
- ✅ Quick `pulumi preview` to verify changes
- ✅ Development/experimentation
- ✅ Troubleshooting issues

**Use GitHub Actions for:**
- ✅ All actual deployments (test/prod)
- ✅ CI/CD pipeline
- ✅ Production deployments
- ✅ Team deployments

## Recommended Workflow

### Phase 1: Initial Setup (Do Once Locally)

```bash
# 1. Test locally first (verify everything works)
cd infrastructure
source .venv/bin/activate
pulumi preview

# 2. If preview looks good, do ONE local deployment to verify
pulumi up
# This ensures your code works before setting up CI/CD
```

### Phase 2: Switch to GitHub Actions (Recommended)

After initial local deployment works:

1. **Commit and push your code**
   ```bash
   git add .
   git commit -m "Initial infrastructure setup"
   git push origin develop  # or test branch
   ```

2. **GitHub Actions will automatically:**
   - Run `pulumi preview` on PRs
   - Run `pulumi up` on pushes to `develop`/`test` branches
   - Deploy to production on pushes to `main`

3. **Future changes:**
   - Make changes locally
   - Test with `pulumi preview` locally
   - Commit and push
   - GitHub Actions deploys automatically

## Current Setup Status

### ✅ Already Configured

- ✅ OIDC setup complete (GitHub → AWS)
- ✅ GitHub Secrets configured (`AWS_ROLE_ARN`, `PULUMI_ACCESS_TOKEN`)
- ✅ GitHub Actions workflows ready (`.github/workflows/test.yml`, `prod.yml`)
- ✅ Workflows configured to use OIDC (no access keys needed)

### What Happens When You Push

**On push to `develop` or `test` branch:**
1. GitHub Actions workflow triggers
2. Checks out your code
3. Authenticates with AWS using OIDC (no credentials needed)
4. Runs `pulumi preview` (if PR) or `pulumi up` (if push)
5. Creates/updates infrastructure
6. Pushes Docker image to ECR
7. Deploys to EC2

## Quick Start: Deploy via GitHub Actions

### Step 1: Verify GitHub Secrets

Go to: https://github.com/tanwardivya/pulumi-provisioning/settings/secrets/actions

Make sure these are set:
- ✅ `PULUMI_ACCESS_TOKEN` - Your Pulumi Cloud token
- ✅ `AWS_ROLE_ARN` - IAM role ARN (from OIDC setup)
- ⚠️ `DB_PASSWORD` - Add your database password (if not set)

### Step 2: Commit and Push

```bash
# Make sure all changes are committed
git status

# Commit if needed
git add .
git commit -m "Initial infrastructure code"

# Push to trigger deployment
git push origin develop
# or
git push origin test
```

### Step 3: Watch Deployment

1. Go to: https://github.com/tanwardivya/pulumi-provisioning/actions
2. Click on the running workflow
3. Watch the deployment progress
4. Check logs if there are errors

## Workflow Comparison

### Local Deployment

```bash
# Pros:
✅ Fast feedback
✅ Easy debugging
✅ No need to commit first

# Cons:
❌ Uses your personal credentials
❌ Not reproducible
❌ Not tracked in git
❌ Manual process
```

### GitHub Actions Deployment

```bash
# Pros:
✅ Automated
✅ Secure (OIDC)
✅ Reproducible
✅ Tracked in git
✅ Team-friendly
✅ Production-ready

# Cons:
❌ Slower feedback (needs to commit/push)
❌ Harder to debug (need to check logs)
```

## Best Practice Workflow

### For Development

1. **Make changes locally**
   ```bash
   # Edit code
   vim infrastructure/components/s3.py
   ```

2. **Test locally (preview only)**
   ```bash
   cd infrastructure
   source .venv/bin/activate
   pulumi preview  # Verify changes look good
   ```

3. **Commit and push**
   ```bash
   git add .
   git commit -m "Update S3 component"
   git push origin develop
   ```

4. **GitHub Actions deploys automatically**
   - Check Actions tab for progress
   - Review logs if needed

### For Production

- Only deploy via GitHub Actions
- Use manual approval (already configured in `prod.yml`)
- Review preview before approving
- All deployments tracked in git

## Troubleshooting GitHub Actions

### If deployment fails:

1. **Check workflow logs**
   - Go to Actions tab
   - Click on failed workflow
   - Review error messages

2. **Common issues:**
   - Missing GitHub Secrets → Add them in Settings → Secrets
   - OIDC not configured → Check `OIDC_SETUP.md`
   - Pulumi config missing → Set in workflow or use `Pulumi.test.yaml`

3. **Test locally first**
   ```bash
   # If GitHub Actions fails, test locally to debug
   pulumi preview
   ```

## Recommendation Summary

**For your first deployment:**
- Option A (Recommended): Deploy via GitHub Actions
  - More secure (OIDC)
  - Sets up proper CI/CD from the start
  - Production-ready approach

- Option B (Alternative): Deploy locally first
  - Good for learning/understanding
  - Faster initial feedback
  - Then switch to GitHub Actions

**For all future deployments:**
- ✅ Always use GitHub Actions
- ✅ Use local only for `pulumi preview` testing

## Next Steps

1. **Verify GitHub Secrets are set** (if not already)
2. **Commit your current code** (if not already committed)
3. **Push to trigger deployment**
4. **Watch GitHub Actions deploy**

Ready to deploy via GitHub Actions? Just push your code! 🚀

