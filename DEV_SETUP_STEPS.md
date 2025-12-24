# Development Setup - Step by Step

## AWS IAM User Creation for Development

### Step 1: Create IAM User in AWS Console

1. **Go to AWS IAM Console**
   - Navigate to: https://console.aws.amazon.com/iam/
   - Or search "IAM" in AWS Console top bar

2. **Create New User**
   - Click **"Users"** in the left sidebar
   - Click **"Create user"** button (top right)

3. **User Details**
   - **User name**: `pulumi-dev-user` (or any name you prefer)
   - Click **"Next"**

4. **Set Permissions**
   - Select **"Attach policies directly"**
   - Search for: `AdministratorAccess`
   - ✅ Check the box next to **"AdministratorAccess"**
   - Click **"Next"**

5. **Review and Create**
   - Review the user details
   - Click **"Create user"**

6. **Create Access Key**
   - After user is created, you'll see the user details page
   - Click **"Security credentials"** tab
   - Scroll down to **"Access keys"** section
   - Click **"Create access key"** button

7. **Select Use Case**
   - Choose: **"Command Line Interface (CLI)"**
   - ✅ Check the confirmation box: "I understand the above recommendation..."
   - Click **"Next"**

8. **Add Description (Optional)**
   - Description: `Pulumi development access key`
   - Click **"Next"**

9. **Download or Copy Credentials** ⚠️ **CRITICAL**
   - You'll see:
     - **Access key ID**: `AKIA...` (starts with AKIA)
     - **Secret access key**: `xxxx...` (long string)
   - **DO ONE OF THESE:**
     - Click **"Download .csv file"** (recommended - saves to Downloads)
     - OR **Copy both values** to a secure location
   - ⚠️ **You CANNOT view the secret key again after this step!**
   - Click **"Done"**

---

## Step 2: Configure AWS CLI

### Option A: Create New Profile (Recommended)

This keeps your existing credentials and creates a separate profile for this project:

```bash
# Create a new profile for Pulumi development
aws configure --profile pulumi-dev

# When prompted, enter:
# AWS Access Key ID: [paste your Access Key ID from Step 1]
# AWS Secret Access Key: [paste your Secret Access Key from Step 1]
# Default region name: us-east-1
# Default output format: json
```

### Option B: Replace Default Profile

If you want to replace your current default credentials:

```bash
# Configure default profile (replaces existing)
aws configure

# Enter the same values as above
```

---

## Step 3: Set Profile as Default (If Using Named Profile)

If you used `--profile pulumi-dev`, set it as default for this project:

```bash
# Add to your shell configuration
echo 'export AWS_PROFILE=pulumi-dev' >> ~/.zshrc

# Reload your shell
source ~/.zshrc

# Or just for this terminal session:
export AWS_PROFILE=pulumi-dev
```

---

## Step 4: Verify Setup

Run these commands to verify everything works:

```bash
# Check current AWS identity
aws sts get-caller-identity

# You should see output like:
# {
#     "UserId": "AIDA...",
#     "Account": "123456789012",
#     "Arn": "arn:aws:iam::123456789012:user/pulumi-dev-user"
# }

# Verify the profile is set (if using named profile)
echo $AWS_PROFILE
# Should show: pulumi-dev

# List all configured profiles
aws configure list-profiles
# Should show: default, pulumi-dev (or your profile name)
```

---

## Step 5: Test Pulumi Can Access AWS

```bash
# Check Pulumi is installed
pulumi version

# Check if logged in to Pulumi Cloud
pulumi whoami

# If not logged in:
pulumi login
# Choose "Log in with browser" (easiest)
```

---

## Quick Verification Script

Run this to verify everything:

```bash
echo "=== AWS Configuration ==="
aws sts get-caller-identity

echo -e "\n=== Current Profile ==="
echo $AWS_PROFILE

echo -e "\n=== Pulumi Status ==="
pulumi whoami

echo -e "\n=== All Set! ==="
```

---

## Troubleshooting

### "Unable to locate credentials"
- Make sure you ran `aws configure --profile pulumi-dev`
- Check if profile exists: `cat ~/.aws/credentials`
- Verify profile name matches: `aws configure list-profiles`

### "Access Denied" errors
- Wait 1-2 minutes after creating IAM user (permissions need to propagate)
- Verify `AdministratorAccess` policy is attached to the user
- Check IAM Console → Users → Your User → Permissions tab

### Wrong account showing
- Check current profile: `echo $AWS_PROFILE`
- Switch profile: `export AWS_PROFILE=pulumi-dev`
- Or use: `aws sts get-caller-identity --profile pulumi-dev`

### Can't see secret key
- ⚠️ Secret keys are only shown once during creation
- If you lost it, you need to:
  1. Go to IAM → Users → Your User → Security credentials
  2. Delete the old access key
  3. Create a new access key
  4. Save it immediately!

---

## What's Next?

Once you've completed these steps:

1. ✅ AWS credentials configured
2. ✅ Pulumi logged in
3. ✅ Git repository initialized
4. ✅ Ready to start building!

Run the verification script:
```bash
./verify-setup.sh
```

Then we can start building the project! 🚀

---

## Summary

**For Development Setup:**
- ✅ Use case: **"Command Line Interface (CLI)"**
- ✅ Policy: **AdministratorAccess** (OK for dev)
- ✅ Profile: **pulumi-dev** (recommended)
- ✅ Region: **us-east-1** (or your preference)

**You're all set for development!** 🎉

