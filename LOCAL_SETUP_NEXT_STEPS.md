# Local Setup - Next Steps

## Current Status ✅

- ✅ OIDC setup complete
- ✅ GitHub Secrets configured (AWS_ROLE_ARN, PULUMI_ACCESS_TOKEN)
- ✅ Pulumi config files ready (Pulumi.test.yaml, Pulumi.prod.yaml)
- ✅ Package structure fixed (types/ → config_types/)
- ✅ GitHub Actions workflows configured

## Step-by-Step Local Setup

### Step 1: Install Infrastructure Dependencies

```bash
cd infrastructure
uv pip install -e ".[dev]"
```

**Expected:** Should install successfully now (types conflict fixed)

### Step 2: Verify AWS Credentials

```bash
# Make sure you're using the correct profile
export AWS_PROFILE=pulumi-dev

# Verify
aws sts get-caller-identity
# Should show: Account: 928618160741, User: pulumi-dev-user
```

### Step 3: Verify Pulumi Login

```bash
pulumi whoami
# Should show your Pulumi username
```

### Step 4: Initialize Test Stack

```bash
cd infrastructure

# Initialize stack
pulumi stack init test

# Verify stack created
pulumi stack ls
```

### Step 5: Configure Test Stack

**Option A: Edit YAML file directly (Recommended)**

```bash
# Edit Pulumi.test.yaml - it already has basic config
# Just add the DB password secret:
pulumi config set --secret dbPassword <your-secure-password>
```

**Option B: Set all config via commands**

```bash
pulumi config set aws:region us-east-1
pulumi config set s3BucketName pulumi-provisioning-test-bucket
pulumi config set dbName pulumi_test_db
pulumi config set --secret dbPassword <your-secure-password>
pulumi config set ecrRepositoryName pulumi-provisioning-test
```

### Step 6: Verify Configuration

```bash
# View all config
pulumi config

# View specific value
pulumi config get s3BucketName
```

### Step 7: Preview Changes (Dry-Run)

```bash
# This shows what will be created WITHOUT actually creating it
pulumi preview

# Or use the verification script
cd ..
./verify-pulumi.sh
```

**What to expect:**
- Shows all resources that will be created (VPC, S3, RDS, EC2, ECR, IAM, etc.)
- Review the output carefully
- No actual changes are made

### Step 8: Deploy Infrastructure

```bash
# After preview looks good, deploy
pulumi up

# Review the plan and type 'yes' to confirm
# Or use --yes to skip confirmation
pulumi up --yes
```

**This will create:**
- VPC with subnets, gateways, security groups
- S3 bucket
- RDS PostgreSQL database
- EC2 instance
- ECR repository
- IAM roles and policies

### Step 9: Get Outputs

```bash
# View all outputs
pulumi stack output

# Get specific outputs
pulumi stack output ec2_public_ip
pulumi stack output s3_bucket_name
pulumi stack output rds_endpoint
pulumi stack output ecr_repository_url
```

## Quick Checklist

- [ ] Install dependencies: `cd infrastructure && uv pip install -e ".[dev]"`
- [ ] Verify AWS profile: `export AWS_PROFILE=pulumi-dev && aws sts get-caller-identity`
- [ ] Verify Pulumi login: `pulumi whoami`
- [ ] Initialize stack: `pulumi stack init test`
- [ ] Set DB password: `pulumi config set --secret dbPassword <password>`
- [ ] Preview changes: `pulumi preview`
- [ ] Deploy: `pulumi up` (after reviewing preview)
- [ ] Get outputs: `pulumi stack output`

## Troubleshooting

### If `uv pip install` fails:
- Make sure you're in `infrastructure/` directory
- Check Python version: `python3 --version` (should be 3.11+)

### If `pulumi stack init` fails:
- Check Pulumi login: `pulumi whoami`
- Check YAML syntax in Pulumi.test.yaml

### If `pulumi preview` fails:
- Check all required config is set: `pulumi config`
- Make sure AWS credentials are valid: `aws sts get-caller-identity`
- Check for missing secrets: `pulumi config get dbPassword` (should not be empty)

## Next Steps After Local Setup

1. **Test the deployment** - Verify resources are created correctly
2. **Test GitHub Actions** - Push to test branch and verify workflow runs
3. **Set up production stack** - Repeat for `prod` stack
4. **Configure domain** - If using Route53/ACM

## GitHub Actions Configuration

After local setup, make sure GitHub Secrets are set:

1. Go to: https://github.com/tanwardivya/pulumi-provisioning/settings/secrets/actions
2. Add secrets:
   - `PULUMI_ACCESS_TOKEN` ✅ (already set)
   - `AWS_ROLE_ARN` ✅ (already set)
   - `DB_PASSWORD` - Add your database password
   - `DOMAIN_NAME` - (Optional) Your domain for production

The workflows will automatically:
- Read config from `Pulumi.test.yaml` / `Pulumi.prod.yaml`
- Override secrets from GitHub Secrets (more secure)
- Deploy infrastructure using the configuration

