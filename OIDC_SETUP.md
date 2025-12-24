# OIDC Setup Guide for GitHub Actions

## What is OIDC?

**OIDC (OpenID Connect)** is a secure authentication protocol that allows GitHub Actions to authenticate with AWS **without storing long-lived access keys**.

### Why Use OIDC?

✅ **Security Benefits:**
- **No access keys to manage** - No risk of keys being leaked or stolen
- **Temporary credentials** - AWS automatically rotates credentials (15 minutes)
- **Least privilege** - IAM roles can be scoped to specific repositories/branches
- **Audit trail** - All actions are logged with clear identity

❌ **Without OIDC (Traditional Method):**
- Store AWS access keys in GitHub Secrets
- Keys never expire (security risk)
- If leaked, attacker has full access
- Hard to rotate

✅ **With OIDC:**
- GitHub Actions requests temporary credentials from AWS
- AWS verifies the request comes from GitHub
- Temporary credentials are issued (valid for 1 hour)
- No keys stored anywhere

---

## Prerequisites

Before setting up OIDC, you need:

### 1. AWS Account Access
- ✅ AWS account with IAM permissions
- ✅ Ability to create IAM roles and identity providers
- ✅ Admin access (or IAM permissions: `iam:CreateRole`, `iam:CreateOpenIDConnectProvider`, `iam:AttachRolePolicy`)

### 2. GitHub Repository
- ✅ GitHub repository created
- ✅ Admin access to repository settings
- ✅ Ability to add secrets

### 3. Basic Understanding
- What IAM roles are (AWS identity with permissions)
- What trust policies are (who can assume the role)
- Basic GitHub Actions workflow structure

---

## Step-by-Step Setup

### Step 1: Create OIDC Identity Provider in AWS

This tells AWS to trust GitHub as an identity provider.

1. **Go to AWS Console**
   - Navigate to: **IAM** → **Identity providers**
   - Or direct link: https://console.aws.amazon.com/iam/home#/providers

2. **Add Provider**
   - Click **"Add provider"** button
   - Select **"OpenID Connect"** tab

3. **Configure Provider**
   - **Provider URL**: `https://token.actions.githubusercontent.com`
   - **Audience**: `sts.amazonaws.com`
   - Click **"Add provider"**

4. **Verify Provider Created**
   - You should see `token.actions.githubusercontent.com` in the list
   - Note the **Provider ARN** (you'll need this later)
   - Format: `arn:aws:iam::YOUR_ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com`

**Screenshot Reference:**
```
Provider URL: https://token.actions.githubusercontent.com
Audience:     sts.amazonaws.com
```

---

### Step 2: Create IAM Role for GitHub Actions

This role will be assumed by GitHub Actions to access AWS.

#### Option A: Using AWS Console (Recommended for Beginners)

1. **Go to IAM Roles**
   - Navigate to: **IAM** → **Roles**
   - Click **"Create role"**

2. **Select Trusted Entity Type**
   - Select **"Web identity"**
   - **Identity provider**: Select `token.actions.githubusercontent.com`
   - **Audience**: `sts.amazonaws.com`

3. **Add Conditions (Optional but Recommended)**
   Click **"Add condition"** to restrict which repositories can use this role:
   
   **Condition 1: Repository**
   - **Condition key**: `StringEquals`
   - **Key**: `token.actions.githubusercontent.com:aud`
   - **Value**: `sts.amazonaws.com`
   
   **Condition 2: Repository Name** (Recommended)
   - **Condition key**: `StringEquals`
   - **Key**: `token.actions.githubusercontent.com:sub`
   - **Value**: `repo:YOUR_GITHUB_USERNAME/YOUR_REPO_NAME:*`
   
   Example: `repo:divyadhara/pulumi-provisioning:*`
   
   This ensures only your repository can use this role.

4. **Add Permissions**
   - Attach the policy you created earlier (e.g., `PulumiInfrastructurePolicy`)
   - Or attach `AdministratorAccess` for development (not recommended for production)

5. **Name the Role**
   - **Role name**: `github-actions-pulumi-role` (or your choice)
   - **Description**: "IAM role for GitHub Actions to deploy infrastructure via Pulumi"

6. **Create Role**
   - Review and click **"Create role"**

7. **Copy Role ARN**
   - After creation, click on the role
   - Copy the **Role ARN** (you'll need this for GitHub Secrets)
   - Format: `arn:aws:iam::YOUR_ACCOUNT_ID:role/github-actions-pulumi-role`

#### Option B: Using AWS CLI

```bash
# Create trust policy file
cat > github-actions-trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::YOUR_ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:YOUR_GITHUB_USERNAME/YOUR_REPO_NAME:*"
        }
      }
    }
  ]
}
EOF

# Create the role
aws iam create-role \
  --role-name github-actions-pulumi-role \
  --assume-role-policy-document file://github-actions-trust-policy.json \
  --description "IAM role for GitHub Actions to deploy infrastructure via Pulumi"

# Attach policy (replace with your policy ARN)
aws iam attach-role-policy \
  --role-name github-actions-pulumi-role \
  --policy-arn arn:aws:iam::aws:policy/AdministratorAccess

# Get the role ARN
aws iam get-role --role-name github-actions-pulumi-role --query 'Role.Arn' --output text
```

---

### Step 3: Get Your AWS Account ID

You'll need this for the trust policy:

```bash
aws sts get-caller-identity --query Account --output text
```

Or find it in the AWS Console (top right corner, next to your username).

---

### Step 4: Add Role ARN to GitHub Secrets

1. **Go to GitHub Repository**
   - Navigate to: **Settings** → **Secrets and variables** → **Actions**

2. **Add New Secret**
   - Click **"New repository secret"**
   - **Name**: `AWS_ROLE_ARN`
   - **Value**: Paste the Role ARN from Step 2
     - Example: `arn:aws:iam::123456789012:role/github-actions-pulumi-role`
   - Click **"Add secret"**

3. **Verify Secret Added**
   - You should see `AWS_ROLE_ARN` in the secrets list

---

### Step 5: Update GitHub Actions Workflow

Your workflow should already be configured! Check that it has:

```yaml
- name: Configure AWS credentials
  uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
    aws-region: us-east-1
```

This step:
1. Requests a token from GitHub
2. Exchanges it for AWS temporary credentials
3. Configures AWS CLI in the workflow

---

## How It Works (Technical Flow)

```
1. GitHub Actions workflow runs
   ↓
2. aws-actions/configure-aws-credentials action:
   - Requests OIDC token from GitHub
   - Token contains: repository, branch, workflow info
   ↓
3. Action calls AWS STS AssumeRoleWithWebIdentity:
   - Sends OIDC token to AWS
   - AWS verifies token signature with GitHub
   ↓
4. AWS checks trust policy:
   - Is the provider trusted? ✅
   - Does the condition match? ✅ (repository, branch, etc.)
   ↓
5. AWS issues temporary credentials:
   - Access Key ID (temporary)
   - Secret Access Key (temporary)
   - Session Token (temporary)
   - Valid for 1 hour
   ↓
6. Workflow uses credentials:
   - Pulumi commands run with temporary credentials
   - All AWS API calls authenticated
   ↓
7. Credentials expire after 1 hour
   - No long-lived keys to manage
```

---

## Advanced: Restricting Access by Branch

You can restrict which branches can use the role by updating the trust policy condition:

```json
{
  "Condition": {
    "StringEquals": {
      "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
      "token.actions.githubusercontent.com:sub": "repo:YOUR_USERNAME/YOUR_REPO:ref:refs/heads/main"
    }
  }
}
```

This ensures only the `main` branch can assume the role.

**For multiple branches:**
```json
{
  "Condition": {
    "StringEquals": {
      "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
    },
    "StringLike": {
      "token.actions.githubusercontent.com:sub": [
        "repo:YOUR_USERNAME/YOUR_REPO:ref:refs/heads/main",
        "repo:YOUR_USERNAME/YOUR_REPO:ref:refs/heads/develop"
      ]
    }
  }
}
```

---

## Troubleshooting

### Error: "Not authorized to perform sts:AssumeRoleWithWebIdentity"

**Cause:** Trust policy conditions don't match

**Fix:**
1. Check the repository name in the condition matches exactly
2. Check the branch name if you restricted by branch
3. Verify the OIDC provider is created correctly

### Error: "The provided token is malformed or invalid"

**Cause:** OIDC provider not configured correctly

**Fix:**
1. Verify provider URL: `https://token.actions.githubusercontent.com`
2. Verify audience: `sts.amazonaws.com`
3. Check provider exists in IAM → Identity providers

### Error: "Access Denied" when running Pulumi

**Cause:** IAM role doesn't have required permissions

**Fix:**
1. Check attached policies on the role
2. Verify the policy has permissions for: EC2, S3, RDS, IAM, ECR, etc.
3. Use the policy from `IAM_PRODUCTION_SETUP.md` or `pulumi-infrastructure-policy.json`

### Error: "Role ARN not found in secrets"

**Cause:** GitHub secret not set correctly

**Fix:**
1. Go to Settings → Secrets → Actions
2. Verify `AWS_ROLE_ARN` exists
3. Check the ARN format is correct (starts with `arn:aws:iam::`)

---

## Verification Steps

### 1. Test OIDC Provider

```bash
# List identity providers
aws iam list-open-id-connect-providers

# Should show:
# {
#   "OpenIDConnectProviderList": [
#     {
#       "Arn": "arn:aws:iam::YOUR_ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"
#     }
#   ]
# }
```

### 2. Test IAM Role

```bash
# Get role details
aws iam get-role --role-name github-actions-pulumi-role

# Check trust policy
aws iam get-role --role-name github-actions-pulumi-role --query 'Role.AssumeRolePolicyDocument'

# List attached policies
aws iam list-attached-role-policies --role-name github-actions-pulumi-role
```

### 3. Test GitHub Actions

1. Push a commit to trigger the workflow
2. Check workflow logs in GitHub Actions
3. Look for "Configure AWS credentials" step
4. Should see: "Successfully configured AWS credentials"

---

## Security Best Practices

### ✅ DO:
- **Restrict by repository** - Only allow your specific repo
- **Restrict by branch** - Only allow main/prod branches for production role
- **Use least privilege** - Attach only necessary policies
- **Separate roles** - Different roles for test/prod environments
- **Monitor usage** - Check CloudTrail logs regularly

### ❌ DON'T:
- Use `*` in repository conditions (allows any repo)
- Use `AdministratorAccess` in production
- Share role ARNs publicly
- Skip condition checks in trust policy

---

## Quick Reference

### Required Values:

1. **OIDC Provider URL**: `https://token.actions.githubusercontent.com`
2. **Audience**: `sts.amazonaws.com`
3. **Repository Condition**: `repo:YOUR_USERNAME/YOUR_REPO_NAME:*`
4. **GitHub Secret Name**: `AWS_ROLE_ARN`
5. **Role ARN Format**: `arn:aws:iam::ACCOUNT_ID:role/ROLE_NAME`

### Commands:

```bash
# Get AWS Account ID
aws sts get-caller-identity --query Account --output text

# List OIDC providers
aws iam list-open-id-connect-providers

# Get role ARN
aws iam get-role --role-name github-actions-pulumi-role --query 'Role.Arn' --output text

# Test role trust policy
aws iam get-role --role-name github-actions-pulumi-role --query 'Role.AssumeRolePolicyDocument'
```

---

## Next Steps

After setting up OIDC:

1. ✅ Test the workflow by pushing a commit
2. ✅ Verify credentials work in GitHub Actions logs
3. ✅ Check CloudTrail to see the AssumeRole calls
4. ✅ Set up separate roles for test/prod if needed

---

## Additional Resources

- [AWS Documentation: Creating OpenID Connect identity providers](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_create_oidc.html)
- [GitHub Actions: Configuring OpenID Connect in Amazon Web Services](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services)
- [AWS IAM Roles](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles.html)

---

## Summary

**OIDC Setup Checklist:**

- [ ] Create OIDC identity provider in AWS IAM
- [ ] Create IAM role with trust policy for GitHub
- [ ] Attach necessary permissions to the role
- [ ] Copy role ARN
- [ ] Add `AWS_ROLE_ARN` to GitHub Secrets
- [ ] Test workflow to verify it works
- [ ] Monitor CloudTrail for security

**You're done!** Your GitHub Actions can now securely access AWS without storing any access keys. 🎉

