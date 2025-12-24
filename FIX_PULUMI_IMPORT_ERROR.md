# Fix: ModuleNotFoundError: No module named 'pulumi'

## Problem
When running `pulumi preview`, you get:
```
ModuleNotFoundError: No module named 'pulumi'
It looks like the Pulumi SDK has not been installed.
```

## Solution

You need to install the Pulumi dependencies in the `infrastructure/` directory.

### Option 1: Using `uv` (Recommended)

```bash
cd /Users/divyadhara/git_repos/pulumi-provisioning/infrastructure
uv pip install -e ".[dev]"
```

### Option 2: Using `pip` with virtual environment

```bash
cd /Users/divyadhara/git_repos/pulumi-provisioning/infrastructure

# Activate virtual environment (if exists)
source .venv/bin/activate

# Or create new one
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -e ".[dev]"
```

### Option 3: Using `pip` system-wide (not recommended)

```bash
cd /Users/divyadhara/git_repos/pulumi-provisioning/infrastructure
pip3 install -e ".[dev]"
```

## Verify Installation

After installing, verify Pulumi is available:

```bash
# Check if pulumi module can be imported
python3 -c "import pulumi; print('✅ Pulumi installed:', pulumi.__version__)"

# Or check installed packages
pip list | grep pulumi
```

## Then Run Pulumi Preview

```bash
# Make sure you're in infrastructure directory
cd /Users/divyadhara/git_repos/pulumi-provisioning/infrastructure

# Select the test stack
pulumi stack select test

# Run preview
pulumi preview
```

## Expected Output

After successful installation, `pulumi preview` should show:
- All resources that will be created (VPC, S3, RDS, EC2, ECR, IAM, etc.)
- No import errors

## Troubleshooting

### If `uv pip install` fails:
- Make sure `uv` is installed: `uv --version`
- Try with `--no-cache` flag: `uv pip install --no-cache -e ".[dev]"`

### If `pip install` fails:
- Check Python version: `python3 --version` (should be 3.11+)
- Try upgrading pip: `pip install --upgrade pip`
- Check if you're in the right directory: `pwd` (should be in `infrastructure/`)

### If Pulumi still can't find modules:
- Make sure you're using the same Python environment where you installed packages
- Check `PYTHONPATH`: `echo $PYTHONPATH`
- Verify installation: `python3 -c "import sys; print(sys.path)"`

