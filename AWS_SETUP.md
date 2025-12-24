# AWS Setup Guide - Creating New IAM User

You don't need a new AWS account! You can create a new IAM user in your existing account. This is the recommended approach for development.

## Option 1: Create New IAM User (Recommended)

### Step 1: Create IAM User in AWS Console

1. **Log in to AWS Console**
   - Go to https://console.aws.amazon.com/
   - Sign in with your existing account

2. **Navigate to IAM**
   - Search for "IAM" in the top search bar
   - Or go to: https://console.aws.amazon.com/iam/

3. **Create New User**
   - Click "Users" in the left sidebar
   - Click "Create user" button

4. **User Details**
   - **User name**: `pulumi-dev-user` (or any name you prefer)
   - **AWS credential type**: Select "Access key - Programmatic access"
   - Click "Next"

5. **Set Permissions**
   - Choose "Attach policies directly"
   - Search for and select: **`AdministratorAccess`**
     - ⚠️ **Note**: This gives full access. For production, use more restrictive policies.
     - For development/testing, AdministratorAccess is fine
   - Click "Next"

6. **Review and Create**
   - Review the user details
   - Click "Create user"

7. **Save Credentials** ⚠️ **IMPORTANT**
   - You'll see the **Access key ID** and **Secret access key**
   - **Download the CSV file** or **copy both values immediately**
   - ⚠️ **You cannot view the secret key again after this step!**
   - Click "Done"

### Step 2: Configure AWS CLI with New Credentials

You have two options:

#### Option A: Replace Default Credentials

```bash
# Configure AWS CLI (this will replace your current default credentials)
aws configure

# When prompted, enter:
# - AWS Access Key ID: [paste your new Access Key ID]
# - AWS Secret Access Key: [paste your new Secret Access Key]
# - Default region name: us-east-1 (or your preferred region)
# - Default output format: json
```

#### Option B: Use Named Profile (Recommended - Keeps Multiple Accounts)

This allows you to keep your existing credentials and use the new user for this project:

```bash
# Configure a named profile for this project
aws configure --profile pulumi-dev

# When prompted, enter:
# - AWS Access Key ID: [paste your new Access Key ID]
# - AWS Secret Access Key: [paste your new Secret Access Key]
# - Default region name: us-east-1
# - Default output format: json
```

Then set environment variable to use this profile:
```bash
export AWS_PROFILE=pulumi-dev
```

Or add to your shell config file (`~/.zshrc` or `~/.bashrc`):
```bash
echo 'export AWS_PROFILE=pulumi-dev' >> ~/.zshrc
source ~/.zshrc
```

### Step 3: Verify New Credentials

```bash
# If using default profile:
aws sts get-caller-identity

# If using named profile:
aws sts get-caller-identity --profile pulumi-dev

# You should see output like:
# {
#     "UserId": "AIDA...",
#     "Account": "123456789012",
#     "Arn": "arn:aws:iam::123456789012:user/pulumi-dev-user"
# }
```

---

## Option 2: Create New AWS Account (If You Really Want Separate Account)

If you prefer a completely separate AWS account:

1. **Create New AWS Account**
   - Go to https://portal.aws.amazon.com/billing/signup
   - Follow the signup process
   - You'll need a different email address and payment method

2. **Configure AWS CLI**
   ```bash
   aws configure --profile new-account
   ```

3. **Use the Profile**
   ```bash
   export AWS_PROFILE=new-account
   ```

---

## Option 3: Use AWS SSO (For Organizations)

If your AWS account is part of an organization with SSO:

```bash
# Configure SSO
aws configure sso

# Follow the prompts to set up SSO
# Then use:
aws sso login --profile your-sso-profile
```

---

## Recommended Approach: Named Profile

I recommend **Option 1B (Named Profile)** because:
- ✅ Keeps your existing credentials intact
- ✅ Easy to switch between accounts/users
- ✅ Better for managing multiple projects
- ✅ No risk of accidentally using wrong credentials

### Setup Named Profile - Quick Commands

```bash
# 1. Create the profile
aws configure --profile pulumi-dev

# 2. Set it as default for this project (add to ~/.zshrc)
echo 'export AWS_PROFILE=pulumi-dev' >> ~/.zshrc
source ~/.zshrc

# 3. Verify it works
aws sts get-caller-identity

# 4. If you need to switch back to your other account:
export AWS_PROFILE=default  # or your other profile name
```

---

## Troubleshooting

### "Unable to locate credentials"
- Make sure you ran `aws configure` (or `aws configure --profile pulumi-dev`)
- Check credentials file: `cat ~/.aws/credentials`
- Verify profile exists: `cat ~/.aws/config`

### "Access Denied" when running commands
- The IAM user might not have the right permissions
- Go back to IAM console and verify `AdministratorAccess` is attached
- Wait a few minutes for permissions to propagate

### Want to see current credentials?
```bash
# Show current identity
aws sts get-caller-identity

# List all configured profiles
aws configure list-profiles

# Show specific profile config
aws configure list --profile pulumi-dev
```

---

## Next Steps

Once you've set up the new IAM user and configured AWS CLI:

1. ✅ Verify credentials: `aws sts get-caller-identity`
2. ✅ Run verification script: `./verify-setup.sh`
3. ✅ Proceed with project setup

Let me know once you've completed the IAM user setup and we can verify everything is working!

