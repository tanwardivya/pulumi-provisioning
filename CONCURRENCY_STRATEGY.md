# Concurrency Strategy for Multiple PRs

## Problem Statement

When multiple developers merge PRs quickly, multiple deployments can run simultaneously, causing:
- ❌ **AWS state conflicts** (two deployments modifying same resources)
- ❌ **Race conditions** (which deployment wins?)
- ❌ **Inconsistent infrastructure state**
- ❌ **Failed deployments** due to resource locks

## Solution: Concurrency Controls

We use GitHub Actions `concurrency` feature to ensure **only one deployment runs at a time**.

---

## How It Works

### Concurrency Groups

Each deployment job has a `concurrency` group that identifies which deployments should be serialized:

```yaml
concurrency:
  group: deploy-test-${{ github.ref }}
  cancel-in-progress: true  # or false
```

**Group Key**: `deploy-test-${{ github.ref }}`
- All deployments to the same branch share the same group
- Different branches can deploy in parallel

---

## Scenarios

### Scenario 1: Two PRs Merged Quickly

**Timeline**:
```
10:00 AM - Developer A merges PR #1 → Deploy starts
10:01 AM - Developer B merges PR #2 → What happens?
```

**With Concurrency Control**:

#### Test Environment (cancel-in-progress: true)
```
10:00 AM - Deploy #1 starts (PR #1)
10:01 AM - Deploy #2 starts (PR #2)
           ↓
           Deploy #1 is CANCELLED
           Deploy #2 continues
           ↓
10:05 AM - Deploy #2 completes
           ✅ Latest code is deployed
```

**Result**: Latest deployment wins (good for test environment)

#### Production Environment (cancel-in-progress: false)
```
10:00 AM - Deploy #1 starts (PR #1)
10:01 AM - Deploy #2 starts (PR #2)
           ↓
           Deploy #2 WAITS in queue
           ↓
10:05 AM - Deploy #1 completes
           ↓
           Deploy #2 starts automatically
           ↓
10:10 AM - Deploy #2 completes
           ✅ Both changes are applied sequentially
```

**Result**: All changes are applied in order (safer for production)

---

### Scenario 2: Multiple PRs Open Simultaneously

**Timeline**:
```
10:00 AM - PR #1 opened → Preview runs
10:01 AM - PR #2 opened → Preview runs
10:02 AM - PR #3 opened → Preview runs
```

**With Concurrency Control**:

```
10:00 AM - Preview #1 runs (PR #1)
10:01 AM - Preview #2 runs (PR #2)  ← Runs in parallel ✅
10:02 AM - Preview #3 runs (PR #3)  ← Runs in parallel ✅

All previews run simultaneously because:
- Each PR has its own concurrency group
- Preview is read-only (safe to run in parallel)
```

**Result**: All previews run in parallel (safe because read-only)

---

### Scenario 3: PR Merged While Deployment Running

**Timeline**:
```
10:00 AM - PR #1 merged → Deploy #1 starts (takes 5 minutes)
10:02 AM - PR #2 merged → Deploy #2 triggered
```

**With Concurrency Control**:

#### Test Environment
```
10:00 AM - Deploy #1 starts
10:02 AM - Deploy #2 starts
           ↓
           Deploy #1 is CANCELLED
           Deploy #2 continues with latest code
           ↓
10:07 AM - Deploy #2 completes
```

**Result**: Only latest code is deployed (avoids partial updates)

#### Production Environment
```
10:00 AM - Deploy #1 starts
10:02 AM - Deploy #2 starts
           ↓
           Deploy #2 WAITS
           ↓
10:05 AM - Deploy #1 completes
           ↓
           Deploy #2 starts automatically
           ↓
10:10 AM - Deploy #2 completes
```

**Result**: Both changes applied sequentially (ensures consistency)

---

## Configuration

### Test Environment

```yaml
concurrency:
  group: deploy-test-${{ github.ref }}
  cancel-in-progress: true  # Latest wins
```

**Strategy**: **Cancel in-progress** deployments
- ✅ Faster (don't wait for old deployment)
- ✅ Always deploys latest code
- ✅ Good for test/staging environments
- ⚠️ Old deployment is cancelled (may leave partial state)

### Production Environment

```yaml
concurrency:
  group: deploy-prod-${{ github.ref }}
  cancel-in-progress: false  # Queue deployments
```

**Strategy**: **Queue** deployments
- ✅ All changes are applied
- ✅ No partial deployments
- ✅ Safer for production
- ⚠️ Slower (must wait for previous to finish)

### Preview Jobs

```yaml
concurrency:
  group: preview-pr-${{ github.event.pull_request.number }}
  cancel-in-progress: false  # Let each preview complete
```

**Strategy**: **Per-PR groups**
- ✅ Each PR has its own group
- ✅ Multiple previews run in parallel
- ✅ Safe because preview is read-only

---

## Visual Flow Diagrams

### Test Environment Flow

```
PR #1 Merged → Deploy #1 Starts
                ↓
PR #2 Merged → Deploy #2 Starts
                ↓
                ├─→ Deploy #1 CANCELLED ❌
                └─→ Deploy #2 Continues ✅
                    ↓
                Deploy #2 Completes
```

### Production Environment Flow

```
PR #1 Merged → Deploy #1 Starts
                ↓
PR #2 Merged → Deploy #2 Starts
                ↓
                Deploy #2 WAITS ⏳
                ↓
            Deploy #1 Completes ✅
                ↓
            Deploy #2 Starts ✅
                ↓
            Deploy #2 Completes ✅
```

### Preview Flow (Multiple PRs)

```
PR #1 Opened → Preview #1 Starts ✅
                ↓
PR #2 Opened → Preview #2 Starts ✅ (parallel)
                ↓
PR #3 Opened → Preview #3 Starts ✅ (parallel)
                ↓
            All Complete ✅
```

---

## Benefits

### ✅ Prevents State Conflicts

**Without concurrency**:
```
Deploy #1: Creating EC2 instance...
Deploy #2: Creating EC2 instance... (same name!)
           ↓
           ❌ Error: Resource already exists
           ❌ State conflict!
```

**With concurrency**:
```
Deploy #1: Creating EC2 instance...
Deploy #2: Waits for Deploy #1 to finish
           ↓
           ✅ No conflicts
           ✅ Clean state
```

### ✅ Ensures Consistency

- Only one deployment modifies AWS at a time
- No race conditions
- Predictable outcomes

### ✅ Better Resource Management

- No wasted resources from cancelled deployments
- Clear deployment order
- Easy to track what's deployed

---

## Best Practices

### ✅ DO:

1. **Use concurrency for all deploy jobs**
   - Prevents state conflicts
   - Ensures consistency

2. **Use cancel-in-progress for test environments**
   - Faster deployments
   - Always deploys latest code

3. **Use queue (cancel-in-progress: false) for production**
   - Ensures all changes are applied
   - Safer for critical environments

4. **Use per-PR groups for previews**
   - Allows parallel previews
   - Safe because read-only

### ❌ DON'T:

1. **Don't skip concurrency controls**
   - Will cause state conflicts
   - Unpredictable behavior

2. **Don't use same group for different environments**
   - Test and prod should have separate groups
   - Allows parallel deployment to different environments

3. **Don't cancel production deployments**
   - Use queue instead
   - Ensures all changes are applied

---

## Monitoring

### Check Deployment Status

In GitHub Actions, you can see:
- Which deployment is running
- Which deployments are queued
- Which deployments were cancelled

### Example Logs

```
🚀 Starting Infrastructure Deployment
==========================================
Stack: test
Branch: develop
Commit: abc123
Triggered by: developer1

ℹ️  Note: Only one deployment runs at a time
   If another deployment is running, this will cancel it
   (latest deployment wins for test environment)
==========================================
```

---

## Troubleshooting

### Issue: Deployment Stuck in Queue

**Symptom**: Deployment shows "Waiting" status

**Cause**: Another deployment is running

**Solution**: Wait for current deployment to finish, or cancel it manually

### Issue: Deployment Cancelled Unexpectedly

**Symptom**: Deployment shows "Cancelled" status

**Cause**: New deployment started while this one was running (cancel-in-progress: true)

**Solution**: This is expected behavior for test environment. Check if newer deployment succeeded.

### Issue: Multiple Deployments Running

**Symptom**: See multiple deployments running simultaneously

**Cause**: Concurrency group not configured correctly

**Solution**: Verify `concurrency.group` is set correctly in workflow

---

## Summary

| Scenario | Without Concurrency | With Concurrency |
|----------|-------------------|------------------|
| 2 PRs merged quickly | ❌ Both deploy → Conflict | ✅ One waits/cancels → No conflict |
| Multiple PRs open | ✅ All preview (read-only) | ✅ All preview (read-only) |
| PR during deployment | ❌ Race condition | ✅ Queued or cancelled |
| State consistency | ❌ Unpredictable | ✅ Always consistent |

**Key Takeaway**: Concurrency controls ensure **only one deployment runs at a time**, preventing AWS state conflicts and ensuring consistent infrastructure! 🎯

