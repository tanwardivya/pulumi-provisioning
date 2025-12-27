# IAM Roles Verification: Test vs Production

## Current Issue

**Both test and production workflows are using the same IAM role!**

- Test workflow: Uses `secrets.AWS_ROLE_ARN`
- Production workflow: Uses `secrets.AWS_ROLE_ARN` (same secret)

This means they have the same permissions, which is not ideal for security.

## Required Setup

### Test Environment
- **Role**: Should have `AdministratorAccess` (OK for test/dev)
- **Secret**: `AWS_ROLE_ARN` (or `AWS_TEST_ROLE_ARN`)

### Production Environment
- **Role**: Should have **limited/custom permissions** (least privilege)
- **Secret**: `AWS_PROD_ROLE_ARN` (separate from test)

## Required Permissions for Production

Based on the infrastructure code, the production role needs:

### 1. EC2 Permissions
```json
{
  "Effect": "Allow",
  "Action": [
    "ec2:*"
  ],
  "Resource": "*"
}
```
**Why**: Create/manage EC2 instances, security groups, VPCs, subnets, internet gateways, NAT gateways, route tables, elastic IPs

### 2. S3 Permissions
```json
{
  "Effect": "Allow",
  "Action": [
    "s3:CreateBucket",
    "s3:DeleteBucket",
    "s3:ListBucket",
    "s3:GetBucketLocation",
    "s3:GetBucketVersioning",
    "s3:PutBucketVersioning",
    "s3:GetBucketPolicy",
    "s3:PutBucketPolicy",
    "s3:DeleteBucketPolicy",
    "s3:GetBucketEncryption",
    "s3:PutBucketEncryption",
    "s3:PutObject",
    "s3:GetObject",
    "s3:DeleteObject",
    "s3:ListObjects",
    "s3:ListObjectsV2"
  ],
  "Resource": [
    "arn:aws:s3:::pulumi-*",
    "arn:aws:s3:::pulumi-*/*"
  ]
}
```
**Why**: Create/manage S3 buckets for file storage

### 3. RDS Permissions
```json
{
  "Effect": "Allow",
  "Action": [
    "rds:CreateDBInstance",
    "rds:DeleteDBInstance",
    "rds:ModifyDBInstance",
    "rds:DescribeDBInstances",
    "rds:CreateDBSubnetGroup",
    "rds:DeleteDBSubnetGroup",
    "rds:DescribeDBSubnetGroups",
    "rds:CreateDBSecurityGroup",
    "rds:DeleteDBSecurityGroup",
    "rds:AuthorizeDBSecurityGroupIngress",
    "rds:RevokeDBSecurityGroupIngress",
    "rds:DescribeDBSecurityGroups"
  ],
  "Resource": "*"
}
```
**Why**: Create/manage PostgreSQL RDS instances

### 4. IAM Permissions (Limited)
```json
{
  "Effect": "Allow",
  "Action": [
    "iam:CreateRole",
    "iam:DeleteRole",
    "iam:AttachRolePolicy",
    "iam:DetachRolePolicy",
    "iam:PutRolePolicy",
    "iam:DeleteRolePolicy",
    "iam:GetRole",
    "iam:GetRolePolicy",
    "iam:ListRolePolicies",
    "iam:ListAttachedRolePolicies",
    "iam:CreateInstanceProfile",
    "iam:DeleteInstanceProfile",
    "iam:AddRoleToInstanceProfile",
    "iam:RemoveRoleFromInstanceProfile",
    "iam:GetInstanceProfile",
    "iam:PassRole"
  ],
  "Resource": [
    "arn:aws:iam::*:role/pulumi-*",
    "arn:aws:iam::*:instance-profile/pulumi-*"
  ],
  "Condition": {
    "StringEquals": {
      "iam:PassedToService": "ec2.amazonaws.com"
    }
  }
}
```
**Why**: Create IAM roles for EC2 instances (to access S3, RDS, ECR)

### 5. ECR Permissions
```json
{
  "Effect": "Allow",
  "Action": [
    "ecr:CreateRepository",
    "ecr:DeleteRepository",
    "ecr:DescribeRepositories",
    "ecr:ListImages",
    "ecr:DescribeImages",
    "ecr:BatchGetImage",
    "ecr:BatchCheckLayerAvailability",
    "ecr:GetDownloadUrlForLayer",
    "ecr:PutImage",
    "ecr:InitiateLayerUpload",
    "ecr:UploadLayerPart",
    "ecr:CompleteLayerUpload",
    "ecr:PutLifecyclePolicy",
    "ecr:GetLifecyclePolicy",
    "ecr:DeleteLifecyclePolicy",
    "ecr:SetRepositoryPolicy",
    "ecr:GetRepositoryPolicy",
    "ecr:DeleteRepositoryPolicy",
    "ecr:PutImageScanningConfiguration",
    "ecr:GetImageScanningConfiguration"
  ],
  "Resource": "arn:aws:ecr:*:*:repository/pulumi-*"
}
```
**Why**: Create/manage ECR repositories, push/pull Docker images

### 6. SSM Permissions
```json
{
  "Effect": "Allow",
  "Action": [
    "ssm:PutParameter",
    "ssm:GetParameter",
    "ssm:GetParameters",
    "ssm:GetParametersByPath",
    "ssm:DeleteParameter",
    "ssm:DescribeParameters",
    "ssm:SendCommand",
    "ssm:GetCommandInvocation",
    "ssm:ListCommandInvocations",
    "ssm:CancelCommand",
    "ssm:DescribeInstanceInformation",
    "ssm:UpdateInstanceInformation"
  ],
  "Resource": [
    "arn:aws:ssm:*:*:parameter/pulumi/*",
    "arn:aws:ssm:*:*:document/AWS-RunShellScript",
    "arn:aws:ec2:*:*:instance/*"
  ]
}
```
**Why**: 
- Store/retrieve database password (`/pulumi/prod/db_password`)
- Store/retrieve image tags (`/pulumi/prod/image_tag`)
- Send SSM commands to EC2 instances for deployment

### 7. Route53 Permissions (Optional)
```json
{
  "Effect": "Allow",
  "Action": [
    "route53:CreateHostedZone",
    "route53:DeleteHostedZone",
    "route53:GetHostedZone",
    "route53:ListHostedZones",
    "route53:ChangeResourceRecordSets",
    "route53:GetChange",
    "route53:ListResourceRecordSets"
  ],
  "Resource": "*"
}
```
**Why**: Manage DNS records (if using custom domain)

### 8. ACM Permissions (Optional)
```json
{
  "Effect": "Allow",
  "Action": [
    "acm:RequestCertificate",
    "acm:DescribeCertificate",
    "acm:ListCertificates",
    "acm:DeleteCertificate",
    "acm:AddTagsToCertificate",
    "acm:RemoveTagsToCertificate"
  ],
  "Resource": "*"
}
```
**Why**: Request/manage SSL certificates (if using HTTPS)

## Missing Permissions Check

The limited production role might be missing:

1. **SSM Permissions** - Critical for:
   - Storing database password
   - Storing image tags
   - Deploying to EC2 via SSM

2. **ECR Permissions** - Critical for:
   - Creating ECR repositories
   - Pushing Docker images
   - Managing image lifecycle

3. **IAM PassRole** - Critical for:
   - Creating EC2 instance roles
   - Attaching policies to roles

## How to Verify

### Step 1: Check Current Roles

```bash
# Check what role test is using
# Go to GitHub: Settings → Secrets → Actions
# Look for: AWS_ROLE_ARN

# Check what role prod is using
# Look for: AWS_PROD_ROLE_ARN (if it exists)
```

### Step 2: Check Role Permissions in AWS

```bash
# List policies attached to test role
aws iam list-attached-role-policies --role-name <test-role-name>

# List policies attached to prod role
aws iam list-attached-role-policies --role-name <prod-role-name>

# Get policy document
aws iam get-policy-version \
  --policy-arn <policy-arn> \
  --version-id <version-id>
```

### Step 3: Test Permissions

Try deploying to production and check for permission errors in the workflow logs.

## Recommended Fix

1. **Create separate secrets**:
   - `AWS_TEST_ROLE_ARN` - For test environment (AdministratorAccess OK)
   - `AWS_PROD_ROLE_ARN` - For production (limited permissions)

2. **Update workflows**:
   - `test.yml`: Use `secrets.AWS_TEST_ROLE_ARN`
   - `prod.yml`: Use `secrets.AWS_PROD_ROLE_ARN`

3. **Verify production role has all required permissions** (listed above)

## Quick Permission Test

Run this to test if the production role has all needed permissions:

```bash
# Test SSM permissions
aws ssm put-parameter \
  --name /pulumi/test-permission-check \
  --value "test" \
  --type String \
  --region us-east-1

# Test ECR permissions
aws ecr describe-repositories --region us-east-1

# Test IAM permissions
aws iam list-roles --query 'Roles[?starts_with(RoleName, `pulumi-`)]'

# Clean up test parameter
aws ssm delete-parameter \
  --name /pulumi/test-permission-check \
  --region us-east-1
```

If any of these fail, the role is missing permissions.

