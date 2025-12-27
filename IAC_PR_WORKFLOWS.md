# Industry Best Practices: IaC PR Workflows

## Overview

This document explains common industry patterns for Infrastructure as Code (IaC) workflows in pull requests, and how our project implements them.

---

## 🏭 Industry Standard Patterns

### 1. **Preview/Plan on PRs (Never Deploy)**

**Pattern**: Always run preview/plan on pull requests, but **never deploy** infrastructure from PRs.

**Why**:
- ✅ **Security**: PRs can come from forks or untrusted sources
- ✅ **Safety**: Shows what will change before merging
- ✅ **Review**: Allows reviewers to see infrastructure impact
- ✅ **Validation**: Catches errors before they reach main branch

**Tools**:
- **Terraform**: `terraform plan`
- **Pulumi**: `pulumi preview`
- **CloudFormation**: `aws cloudformation validate-template`
- **Ansible**: `ansible-playbook --check`

**Our Implementation**:
```yaml
preview:
  if: github.event_name == 'pull_request'
  # Runs pulumi preview to show changes
  # Never deploys infrastructure
```

---

### 2. **Deploy Only After Merge**

**Pattern**: Deploy infrastructure only after PR is merged to target branch.

**Why**:
- ✅ **Trust**: Only deploy code that's been reviewed and merged
- ✅ **Security**: Prevents malicious code from deploying infrastructure
- ✅ **Audit**: Clear history of what was deployed and when
- ✅ **Rollback**: Easier to track and revert changes

**Flow**:
```
PR Created → Preview Runs → Review → Merge → Push Event → Deploy
```

**Our Implementation**:
```yaml
deploy:
  if: github.event_name == 'push'
  # Only runs after PR is merged
  # Deploys to test environment
```

---

### 3. **Status Checks for Branch Protection**

**Pattern**: Use preview results as required status checks for branch protection.

**Why**:
- ✅ **Quality Gate**: Prevents merging broken infrastructure code
- ✅ **Automation**: Enforces best practices automatically
- ✅ **Visibility**: Shows preview status on PR

**GitHub Branch Protection**:
```
Required Status Checks:
  ✅ Pulumi Preview (test)
  ✅ Pulumi Preview (prod)
```

**Our Implementation**:
- Preview job runs on PRs
- Can be configured as required status check
- Fails if preview has errors

---

### 4. **Separate Preview and Deploy Jobs**

**Pattern**: Keep preview and deploy as separate jobs with different triggers.

**Why**:
- ✅ **Clarity**: Clear separation of concerns
- ✅ **Security**: Different permissions for preview vs deploy
- ✅ **Flexibility**: Can run preview without deploying
- ✅ **Performance**: Preview is faster (no actual changes)

**Our Implementation**:
```yaml
jobs:
  preview:    # Runs on PR
  deploy:     # Runs on push
```

---

### 5. **No Secrets in PR Workflows**

**Pattern**: PRs from forks should not have access to secrets.

**Why**:
- ✅ **Security**: Prevents secret leakage from forks
- ✅ **Compliance**: Meets security audit requirements
- ✅ **Best Practice**: Industry standard security practice

**GitHub Behavior**:
- PRs from forks: Secrets are masked/not available
- PRs from same repo: Secrets are available (trusted)

**Our Implementation**:
- Uses OIDC (no long-lived secrets)
- Secrets only used in deploy job (after merge)
- Preview uses read-only permissions

---

### 6. **Preview Output in PR Comments (Optional)**

**Pattern**: Some tools automatically comment preview results on PRs.

**Why**:
- ✅ **Visibility**: Easy to see changes without checking logs
- ✅ **Review**: Reviewers can see infrastructure impact inline
- ✅ **Documentation**: Historical record of what changed

**Tools that support this**:
- Terraform Cloud
- Atlantis (for Terraform)
- Custom GitHub Actions

**Our Implementation**:
- Preview output shown in workflow logs
- Can be extended to comment on PRs (future enhancement)

---

## 📊 Comparison: Industry vs Our Implementation

| Pattern | Industry Standard | Our Implementation | Status |
|---------|------------------|-------------------|--------|
| Preview on PR | ✅ Always | ✅ Yes | ✅ Aligned |
| Deploy on PR | ❌ Never | ❌ No | ✅ Aligned |
| Deploy after merge | ✅ Always | ✅ Yes | ✅ Aligned |
| Status checks | ✅ Recommended | ⚠️ Can be added | ⚠️ Optional |
| Separate jobs | ✅ Recommended | ✅ Yes | ✅ Aligned |
| No secrets in PR | ✅ Required | ✅ Yes | ✅ Aligned |
| PR comments | ⚠️ Optional | ❌ No | ⚠️ Future |

---

## 🔄 Typical Workflow Flow

### Industry Standard Flow:

```
1. Developer creates PR
   ↓
2. Preview/Plan runs automatically
   ↓
3. Preview shows what will change
   ↓
4. Reviewers review code + preview
   ↓
5. Status checks must pass
   ↓
6. PR is merged
   ↓
7. Push event triggers deploy
   ↓
8. Infrastructure is deployed
```

### Our Flow:

```
1. Developer creates PR to develop
   ↓
2. Preview job runs (pulumi preview)
   ↓
3. Preview shows changes
   ↓
4. Reviewers review
   ↓
5. PR is merged
   ↓
6. Push to develop triggers deploy
   ↓
7. Deploy job runs (pulumi up)
   ↓
8. Infrastructure deployed to test
```

---

## 🛡️ Security Considerations

### What We Do Right:

1. ✅ **No deploy from PRs**: Prevents untrusted code from deploying
2. ✅ **OIDC authentication**: No long-lived secrets
3. ✅ **Separate permissions**: Preview has read-only, deploy has write
4. ✅ **Preview validation**: Catches errors before merge

### Additional Recommendations:

1. **Branch Protection Rules**:
   - Require preview to pass before merge
   - Require code review
   - Prevent force push

2. **Environment Protection**:
   - Production requires manual approval
   - Test can auto-deploy

3. **Audit Logging**:
   - Log who triggered deployments
   - Track all infrastructure changes

---

## 📝 Best Practices Summary

### ✅ DO:

- Run preview/plan on every PR
- Deploy only after merge
- Use status checks for quality gates
- Keep preview and deploy separate
- Show preview output clearly
- Fail preview on errors
- Use least privilege permissions

### ❌ DON'T:

- Deploy infrastructure from PRs
- Skip preview on PRs
- Use long-lived secrets
- Give PRs write permissions
- Deploy without review
- Ignore preview errors

---

## 🔧 Configuration Recommendations

### GitHub Branch Protection:

```yaml
# Settings → Branches → Branch protection rules
Branch: develop
  ✅ Require pull request reviews
  ✅ Require status checks to pass
    - Pulumi Preview (test)
  ✅ Require branches to be up to date
  ✅ Do not allow bypassing
```

### Workflow Permissions:

```yaml
# Preview job (read-only)
permissions:
  id-token: write      # For OIDC
  contents: read       # Read code
  pull-requests: write # Comment on PRs (optional)

# Deploy job (write access)
permissions:
  id-token: write      # For OIDC
  contents: read       # Read code
  # No pull-requests needed
```

---

## 🚀 Future Enhancements

1. **PR Comments**: Automatically comment preview results on PRs
2. **Status Checks**: Configure as required status check
3. **Preview Artifacts**: Save preview output as artifact
4. **Cost Estimation**: Show estimated cost changes in preview
5. **Policy Checks**: Run policy validation in preview

---

## 📚 References

- [Pulumi CI/CD Best Practices](https://www.pulumi.com/docs/guides/continuous-delivery/)
- [Terraform Cloud PR Workflows](https://www.terraform.io/docs/cloud/run/ui.html)
- [GitHub Actions Security](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions)
- [IaC Security Best Practices](https://owasp.org/www-project-top-10-risks-for-infrastructure-as-code/)

---

## Summary

Our workflow follows industry best practices:

✅ **Preview on PRs** - Shows changes before merge  
✅ **Deploy after merge** - Only trusted code deploys  
✅ **Separate jobs** - Clear separation of concerns  
✅ **Security first** - No secrets in PRs, OIDC auth  
✅ **Validation** - Preview catches errors early  

This ensures safe, secure, and reliable infrastructure deployments! 🎯

