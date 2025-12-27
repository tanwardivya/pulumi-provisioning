# Fix: Pulumi Not Using Correct Virtual Environment

## Problem
Pulumi is using system Python (`/usr/local/bin/pulumi-language-python-exec`) instead of the virtual environment where Pulumi is installed.

Error:
```
ModuleNotFoundError: No module named 'pulumi'
```

## Solution

### Option 1: Activate Virtual Environment (Recommended)

**Always activate the venv before running Pulumi commands:**

```bash
cd /Users/divyadhara/git_repos/pulumi-provisioning/infrastructure

# Activate the virtual environment
source .venv/bin/activate

# Verify Pulumi is available
python -c "import pulumi; print('✅ Pulumi available')"

# Now run Pulumi commands
pulumi stack select test
pulumi preview
```

### Option 2: Set PULUMI_PYTHON_CMD Environment Variable

```bash
cd /Users/divyadhara/git_repos/pulumi-provisioning/infrastructure

# Point Pulumi to use the venv Python
export PULUMI_PYTHON_CMD="$(pwd)/.venv/bin/python"

# Verify
echo $PULUMI_PYTHON_CMD

# Run Pulumi commands
pulumi preview
```

### Option 3: Use Full Path in Pulumi.yaml (Already Updated)

The `Pulumi.yaml` has been updated to use `infrastructure/.venv` as the virtualenv path. However, you still need to make sure the venv exists and has Pulumi installed.

## Complete Setup Steps

```bash
# 1. Go to infrastructure directory
cd /Users/divyadhara/git_repos/pulumi-provisioning/infrastructure

# 2. Activate virtual environment
source .venv/bin/activate

# 3. Verify Pulumi is installed
python -c "import pulumi; import pulumi_aws; print('✅ All good')"

# 4. Set DB password (if not already set)
pulumi config set --secret dbPassword <your-password>

# 5. Run preview
pulumi preview

# 6. Deploy (after reviewing preview)
pulumi up
```

## Quick Alias (Optional)

Add this to your `~/.zshrc` to make it easier:

```bash
# Pulumi helper
alias pulumi-infra='cd /Users/divyadhara/git_repos/pulumi-provisioning/infrastructure && source .venv/bin/activate'
```

Then just run:
```bash
pulumi-infra
pulumi preview
```

## Verify It's Working

After activating venv, you should see:

```bash
$ source .venv/bin/activate
(.venv) $ python -c "import pulumi; print(pulumi.__file__)"
/Users/divyadhara/git_repos/pulumi-provisioning/infrastructure/.venv/lib/python3.11/site-packages/pulumi/__init__.py

$ pulumi preview
# Should work without errors
```

## Why This Happens

- Pulumi CLI uses the system Python by default
- When you install packages in a venv, they're only available in that venv
- You need to either:
  - Activate the venv (so `python` points to venv Python)
  - Or tell Pulumi which Python to use via `PULUMI_PYTHON_CMD`

## Best Practice

**Always activate the virtual environment before running Pulumi commands:**

```bash
cd infrastructure
source .venv/bin/activate
pulumi preview
```

This ensures Pulumi uses the correct Python interpreter with all dependencies installed.

