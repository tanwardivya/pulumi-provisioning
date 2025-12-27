# Security Guidelines

## Never Commit Secrets

**IMPORTANT:** Never commit the following to git:

- AWS Access Keys and Secret Keys
- Database passwords
- API tokens
- Private keys
- Any sensitive credentials

## Files to Never Commit

The following files are in `.gitignore` and should NOT be committed:

- `setup-aws.sh` - Contains AWS credentials (use `setup-aws.example.sh` as template)
- `*_accessKeys.csv` - AWS access key files
- `*.pem`, `*.key` - Private keys
- `.env` - Environment variables with secrets
- `credentials` - Credential files

## Safe Setup Process

1. **Copy the example file:**
   ```bash
   cp setup-aws.example.sh setup-aws.sh
   ```

2. **Set credentials via environment variables:**
   ```bash
   export AWS_ACCESS_KEY_ID="your-key-id"
   export AWS_SECRET_ACCESS_KEY="your-secret-key"
   ./setup-aws.sh
   ```

3. **Or run interactively:**
   ```bash
   ./setup-aws.sh
   # It will prompt for credentials
   ```

## Managing Secrets

### For Local Development:
- Use environment variables
- Use AWS profiles (`aws configure --profile`)
- Never hardcode in scripts

### For CI/CD:
- Use GitHub Secrets
- Use AWS OIDC (no long-lived keys)
- Use Pulumi secrets (`pulumi config set --secret`)

### For Production:
- Use AWS Systems Manager Parameter Store
- Use AWS Secrets Manager
- Use IAM roles (not access keys)
- Rotate credentials regularly

## If You Accidentally Committed Secrets

1. **Immediately rotate/revoke the exposed credentials**
2. **Remove from git history:**
   ```bash
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch setup-aws.sh" \
     --prune-empty --tag-name-filter cat -- --all
   ```
3. **Force push (coordinate with team):**
   ```bash
   git push origin --force --all
   ```
4. **Update .gitignore** to prevent future commits

## Best Practices

- ✅ Use environment variables
- ✅ Use AWS profiles
- ✅ Use OIDC for CI/CD
- ✅ Use Pulumi secrets for sensitive config
- ✅ Rotate credentials every 90 days
- ❌ Never hardcode credentials
- ❌ Never commit credential files
- ❌ Never share credentials in chat/email

