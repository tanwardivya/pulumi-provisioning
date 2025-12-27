# Deployment Workflow: Test → Integration Tests → Production

## Overview

This document explains the complete deployment workflow from merge to production, including integration tests and manual approval.

---

## 🔄 Complete Workflow Flow

```
┌─────────────────────────────────────────────────────────────┐
│  Step 1: PR Created                                         │
│  └─→ Preview runs (shows infrastructure changes)           │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 2: PR Merged to develop/test                          │
│  └─→ Push event triggers test workflow                      │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 3: Test Environment Deployment                        │
│  ├─→ Deploy infrastructure (EC2, RDS, S3, etc.)           │
│  ├─→ Build Docker image                                     │
│  ├─→ Push to ECR                                            │
│  └─→ Deploy container to EC2                                │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 4: Integration Tests                                  │
│  ├─→ Wait for FastAPI service to be ready                   │
│  ├─→ Test /health endpoint                                  │
│  ├─→ Test /db/status endpoint                               │
│  ├─→ Test /s3/list endpoint                                │
│  ├─→ Test /db/create endpoint                               │
│  └─→ Test /db/read endpoint                                 │
└──────────────────┬──────────────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
        ▼                     ▼
   ┌─────────┐         ┌──────────┐
   │  Pass   │         │   Fail   │
   │         │         │          │
   └────┬────┘         └────┬─────┘
        │                   │
        │                   └─→ ❌ Stop - No production deploy
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 5: Production Workflow Triggered                      │
│  └─→ Automatically triggered when tests pass                │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 6: Manual Approval Required                           │
│  └─→ Reviewer must approve in GitHub                        │
│      (Set in Environment settings)                          │
└──────────────────┬──────────────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
        ▼                     ▼
   ┌─────────┐         ┌──────────┐
   │Approved │         │Rejected  │
   │         │         │          │
   └────┬────┘         └────┬─────┘
        │                   │
        │                   └─→ ❌ Stop - No deployment
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 7: Production Deployment                              │
│  ├─→ Deploy infrastructure to production                   │
│  ├─→ Build Docker image                                     │
│  ├─→ Push to ECR                                            │
│  └─→ Deploy container to EC2                                │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 Integration Tests

### What Gets Tested

After deployment to test environment, the following endpoints are tested:

1. **Health Check** (`GET /health`)
   - Verifies service is running
   - Checks application status

2. **Database Status** (`GET /db/status`)
   - Verifies database connection
   - Ensures RDS is accessible

3. **S3 List** (`GET /s3/list`)
   - Verifies S3 bucket access
   - Tests AWS permissions

4. **Create Record** (`POST /db/create`)
   - Tests database write operations
   - Verifies data persistence

5. **Read Records** (`GET /db/read`)
   - Tests database read operations
   - Verifies data retrieval

### Test Results

- ✅ **All tests pass**: Production workflow is triggered automatically
- ❌ **Any test fails**: Production workflow is NOT triggered

---

## 🚀 Production Deployment

### Automatic Trigger

Production workflow is automatically triggered when:
- ✅ Test workflow completes successfully
- ✅ Integration tests pass
- ✅ All jobs in test workflow succeed

### Manual Approval

**Before production deployment starts**, a reviewer must approve:

1. Go to GitHub Actions
2. Find the production workflow run
3. Click "Review deployments"
4. Approve or reject

**Setup Required**:
- Go to: Repository → Settings → Environments → production
- Add required reviewers
- Enable "Required reviewers"

### Manual Triggers

Production can also be triggered manually:
- **workflow_dispatch**: Manual trigger from Actions UI
- **push to main/master**: Direct deployment (bypasses test)

---

## ⚙️ Configuration

### Setting Up Manual Approval

1. **Go to GitHub Repository Settings**
   - Navigate to: Settings → Environments

2. **Create/Edit Production Environment**
   - Click "New environment" or edit "production"
   - Name: `production`

3. **Add Required Reviewers**
   - Under "Required reviewers"
   - Add team members or individuals
   - Minimum: 1 reviewer

4. **Save Settings**
   - Click "Save protection rules"

**Result**: Every production deployment will wait for approval before starting.

---

## 🔍 Workflow Details

### Test Workflow (`test.yml`)

**Jobs**:
1. **preview** (on PR only)
   - Shows infrastructure changes
   - Read-only, safe to run in parallel

2. **deploy** (on push)
   - Deploys to test environment
   - Builds and pushes Docker image
   - Updates container on EC2

3. **integration-tests** (on push, after deploy)
   - Waits for service to be ready
   - Tests all FastAPI endpoints
   - Fails if any test fails

### Production Workflow (`prod.yml`)

**Triggers**:
- `workflow_run`: When test workflow succeeds
- `workflow_dispatch`: Manual trigger
- `push`: Push to main/master

**Job**:
- **deploy** (requires manual approval)
   - Deploys to production environment
   - Same steps as test deployment
   - Waits for approval before starting

---

## 📊 Example Timeline

### Successful Deployment

```
10:00 AM - PR #1 merged to develop
10:01 AM - Test workflow starts
10:05 AM - Test deployment completes
10:06 AM - Integration tests start
10:08 AM - ✅ All tests pass
10:08 AM - Production workflow triggered
10:08 AM - ⏸️  Waiting for manual approval
10:15 AM - ✅ Reviewer approves
10:15 AM - Production deployment starts
10:20 AM - ✅ Production deployment completes
```

### Failed Integration Tests

```
10:00 AM - PR #1 merged to develop
10:01 AM - Test workflow starts
10:05 AM - Test deployment completes
10:06 AM - Integration tests start
10:08 AM - ❌ Health check fails
10:08 AM - ❌ Integration tests fail
10:08 AM - Production workflow NOT triggered
10:08 AM - Developer fixes issue
10:30 AM - New PR created...
```

---

## 🛡️ Safety Features

### 1. Integration Tests as Gate

- ✅ Production only deploys if tests pass
- ✅ Catches issues before production
- ✅ Validates actual service functionality

### 2. Manual Approval

- ✅ Human review before production
- ✅ Prevents accidental deployments
- ✅ Audit trail of who approved

### 3. Concurrency Control

- ✅ Only one deployment at a time
- ✅ Prevents state conflicts
- ✅ Queue or cancel based on environment

---

## 🔧 Troubleshooting

### Issue: Integration Tests Fail

**Symptoms**:
- Tests fail with HTTP errors
- Service not responding

**Solutions**:
1. Check EC2 instance is running
2. Verify container is running: `docker ps`
3. Check service logs: `docker logs fastapi-app`
4. Verify security groups allow traffic
5. Check database connectivity

### Issue: Production Not Triggered

**Symptoms**:
- Test workflow succeeds
- Production workflow doesn't start

**Solutions**:
1. Check integration tests passed (not just deploy)
2. Verify workflow_run trigger is configured
3. Check GitHub Actions permissions
4. Review workflow logs for errors

### Issue: Manual Approval Not Showing

**Symptoms**:
- Production workflow runs without approval

**Solutions**:
1. Verify environment is named "production" exactly
2. Check environment has required reviewers set
3. Verify workflow uses `environment: production`
4. Check repository settings → Environments

---

## 📝 Best Practices

### ✅ DO:

1. **Always run integration tests**
   - Don't skip tests
   - Fix failing tests before production

2. **Review before approving**
   - Check what changed
   - Verify test results
   - Review deployment plan

3. **Monitor deployments**
   - Watch test deployment
   - Monitor integration tests
   - Verify production after deploy

### ❌ DON'T:

1. **Don't approve without review**
   - Always check what's deploying
   - Verify tests passed

2. **Don't skip integration tests**
   - Tests validate actual functionality
   - Critical for production safety

3. **Don't deploy directly to prod**
   - Always go through test first
   - Use manual trigger only for emergencies

---

## Summary

**Complete Flow**:
1. PR → Preview
2. Merge → Test Deploy
3. Integration Tests
4. If Pass → Production Triggered
5. Manual Approval Required
6. Production Deploy

**Key Benefits**:
- ✅ Tests validate functionality
- ✅ Manual approval prevents mistakes
- ✅ Automatic flow reduces manual work
- ✅ Safety gates at every step

This ensures only tested, approved code reaches production! 🎯

