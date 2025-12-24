# Production-Ready IAM Setup Guide

## ⚠️ Security Best Practices

**AdministratorAccess is NOT for production!** It violates the principle of least privilege.

## Development vs Production Setup

### Development/Testing (Current Setup)
- ✅ `AdministratorAccess` is acceptable for:
  - Local development
  - Learning/experimentation
  - Testing infrastructure
  - Quick prototyping

### Production (What You Should Use)
- ❌ **Never use AdministratorAccess in production**
- ✅ Use **least privilege** - only grant permissions needed for the task
- ✅ Separate IAM users/roles for different purposes
- ✅ Use IAM roles (not users) when possible
- ✅ Enable MFA for production access
- ✅ Use temporary credentials (STS) instead of long-lived keys

---

## Production-Ready IAM Policy

Here's a **custom IAM policy** that grants only the permissions needed for this project:

### Required Permissions for This Project

Based on our infrastructure needs:
- **EC2**: Create, modify, terminate instances, manage security groups
- **S3**: Create buckets, manage objects, set policies
- **RDS**: Create, modify databases, manage snapshots
- **IAM**: Create roles and policies (for EC2 instance roles)
- **VPC**: Create and manage networking resources
- **Route53**: Manage DNS records and hosted zones
- **ACM**: Request and manage SSL certificates
- **CloudWatch**: View logs (optional but recommended)

### Custom IAM Policy JSON

Save this as `pulumi-infrastructure-policy.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "EC2FullAccess",
      "Effect": "Allow",
      "Action": [
        "ec2:*"
      ],
      "Resource": "*"
    },
    {
      "Sid": "S3FullAccess",
      "Effect": "Allow",
      "Action": [
        "s3:*"
      ],
      "Resource": "*"
    },
    {
      "Sid": "RDSFullAccess",
      "Effect": "Allow",
      "Action": [
        "rds:*"
      ],
      "Resource": "*"
    },
    {
      "Sid": "IAMForEC2Roles",
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
    },
    {
      "Sid": "Route53FullAccess",
      "Effect": "Allow",
      "Action": [
        "route53:*"
      ],
      "Resource": "*"
    },
    {
      "Sid": "ACMCertificateManagement",
      "Effect": "Allow",
      "Action": [
        "acm:RequestCertificate",
        "acm:DescribeCertificate",
        "acm:ListCertificates",
        "acm:DeleteCertificate",
        "acm:AddTagsToCertificate",
        "acm:RemoveTagsFromCertificate"
      ],
      "Resource": "*"
    },
    {
      "Sid": "CloudWatchLogs",
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "logs:DescribeLogGroups",
        "logs:DescribeLogStreams"
      ],
      "Resource": "*"
    }
  ]
}
```

### More Restrictive Production Policy (Recommended)

For even better security, use resource-specific permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "EC2Management",
      "Effect": "Allow",
      "Action": [
        "ec2:RunInstances",
        "ec2:TerminateInstances",
        "ec2:StartInstances",
        "ec2:StopInstances",
        "ec2:DescribeInstances",
        "ec2:DescribeImages",
        "ec2:DescribeInstanceTypes",
        "ec2:AllocateAddress",
        "ec2:ReleaseAddress",
        "ec2:AssociateAddress",
        "ec2:DisassociateAddress",
        "ec2:DescribeAddresses",
        "ec2:CreateSecurityGroup",
        "ec2:DeleteSecurityGroup",
        "ec2:AuthorizeSecurityGroupIngress",
        "ec2:RevokeSecurityGroupIngress",
        "ec2:DescribeSecurityGroups",
        "ec2:CreateTags",
        "ec2:DescribeTags"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "ec2:ResourceTag/ManagedBy": "Pulumi"
        }
      }
    },
    {
      "Sid": "VPCManagement",
      "Effect": "Allow",
      "Action": [
        "ec2:CreateVpc",
        "ec2:DeleteVpc",
        "ec2:DescribeVpcs",
        "ec2:CreateSubnet",
        "ec2:DeleteSubnet",
        "ec2:DescribeSubnets",
        "ec2:CreateInternetGateway",
        "ec2:DeleteInternetGateway",
        "ec2:AttachInternetGateway",
        "ec2:DetachInternetGateway",
        "ec2:DescribeInternetGateways",
        "ec2:CreateNatGateway",
        "ec2:DeleteNatGateway",
        "ec2:DescribeNatGateways",
        "ec2:CreateRouteTable",
        "ec2:DeleteRouteTable",
        "ec2:DescribeRouteTables",
        "ec2:CreateRoute",
        "ec2:DeleteRoute",
        "ec2:AssociateRouteTable",
        "ec2:DisassociateRouteTable"
      ],
      "Resource": "*"
    },
    {
      "Sid": "S3BucketManagement",
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
    },
    {
      "Sid": "RDSManagement",
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
    },
    {
      "Sid": "IAMForEC2Roles",
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
    },
    {
      "Sid": "Route53Management",
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
    },
    {
      "Sid": "ACMCertificateManagement",
      "Effect": "Allow",
      "Action": [
        "acm:RequestCertificate",
        "acm:DescribeCertificate",
        "acm:ListCertificates",
        "acm:DeleteCertificate"
      ],
      "Resource": "*"
    }
  ]
}
```

---

## How to Set Up Production IAM User

### Step 1: Create Custom Policy in AWS Console

1. Go to **IAM Console** → **Policies** → **Create policy**
2. Click **JSON** tab
3. Paste one of the policy JSONs above
4. Click **Next**
5. Name: `PulumiInfrastructurePolicy` (or your choice)
6. Description: "Permissions for Pulumi infrastructure provisioning"
7. Click **Create policy**

### Step 2: Create IAM User with Custom Policy

1. Go to **IAM Console** → **Users** → **Create user**
2. User name: `pulumi-infrastructure-user`
3. Select **Access key - Programmatic access**
4. Click **Next**
5. **Attach policies directly**
6. Search for your custom policy: `PulumiInfrastructurePolicy`
7. Select it and click **Next**
8. Review and **Create user**
9. **Save the Access Key ID and Secret Access Key**

### Step 3: Enable MFA (Multi-Factor Authentication) - Recommended

1. After creating user, click on the user name
2. Go to **Security credentials** tab
3. Click **Assign MFA device**
4. Choose **Virtual MFA device** (use Google Authenticator or Authy)
5. Scan QR code and enter two consecutive codes
6. Click **Assign MFA device**

### Step 4: Configure AWS CLI

```bash
# Create profile for production user
aws configure --profile pulumi-prod

# Enter credentials from Step 2
# Region: us-east-1 (or your region)
# Output: json
```

---

## Best Practices Summary

### ✅ DO:
- Use **least privilege** - only grant needed permissions
- Use **IAM roles** instead of users when possible (for EC2, Lambda, etc.)
- Enable **MFA** for production users
- Use **named profiles** to separate dev/prod credentials
- **Tag resources** for better organization and cost tracking
- **Rotate access keys** regularly (every 90 days)
- Use **temporary credentials** (STS) via roles when possible
- **Review permissions** regularly and remove unused ones

### ❌ DON'T:
- Use `AdministratorAccess` in production
- Share access keys between team members
- Commit access keys to git (use secrets management)
- Use root account credentials for daily operations
- Create users with more permissions than needed
- Use long-lived credentials when temporary ones work

---

## For This Project: Recommended Setup

### Development Environment
- ✅ Use `AdministratorAccess` for now (learning/development)
- ✅ Use profile: `pulumi-dev`

### Production Environment
- ✅ Create custom policy (use the JSON above)
- ✅ Create separate IAM user: `pulumi-prod-user`
- ✅ Use profile: `pulumi-prod`
- ✅ Enable MFA
- ✅ Use GitHub Actions with OIDC (no long-lived keys!)

---

## GitHub Actions OIDC (Best Practice)

For CI/CD, **don't use access keys at all!** Use OIDC:

1. **Create IAM Role** (not user) for GitHub Actions
2. **Trust policy** allows GitHub to assume the role
3. **No access keys needed** - GitHub Actions uses temporary credentials
4. **More secure** - credentials rotate automatically

We'll set this up when we create the GitHub Actions workflows.

---

## Quick Reference

```bash
# Development (AdministratorAccess - OK for dev)
aws configure --profile pulumi-dev

# Production (Custom policy - use this for prod)
aws configure --profile pulumi-prod

# Switch between profiles
export AWS_PROFILE=pulumi-dev    # for development
export AWS_PROFILE=pulumi-prod   # for production

# Verify current identity
aws sts get-caller-identity
```

---

## Summary

- **Development**: `AdministratorAccess` is fine for learning
- **Production**: Use custom policy with least privilege
- **CI/CD**: Use OIDC roles (no access keys)
- **Best Practice**: Separate users/profiles for dev and prod

Would you like me to help you create the custom policy and set up the production user?

