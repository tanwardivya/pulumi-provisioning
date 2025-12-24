#!/bin/bash
# Script to verify Pulumi setup and preview changes before deploying

set -e

echo "=== Pulumi Verification Script ==="
echo ""

# Check if we're in the right directory
if [ ! -f "Pulumi.yaml" ]; then
    echo "❌ Error: Pulumi.yaml not found. Run this from project root or infrastructure directory."
    exit 1
fi

# Change to infrastructure directory if needed
if [ -d "infrastructure" ]; then
    cd infrastructure
fi

echo "1. Checking Pulumi installation..."
if ! command -v pulumi &> /dev/null; then
    echo "❌ Pulumi CLI not found. Install it first:"
    echo "   brew install pulumi"
    echo "   or: curl -fsSL https://get.pulumi.com | sh"
    exit 1
fi
echo "✅ Pulumi CLI found: $(pulumi version)"
echo ""

echo "2. Checking Pulumi login..."
if ! pulumi whoami &> /dev/null; then
    echo "❌ Not logged in to Pulumi. Run: pulumi login"
    exit 1
fi
echo "✅ Logged in as: $(pulumi whoami)"
echo ""

echo "3. Checking AWS credentials..."
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials not configured. Run:"
    echo "   export AWS_PROFILE=pulumi-dev"
    echo "   or: aws configure"
    exit 1
fi
AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
AWS_USER=$(aws sts get-caller-identity --query Arn --output text)
echo "✅ AWS credentials valid"
echo "   Account: $AWS_ACCOUNT"
echo "   User: $AWS_USER"
echo ""

echo "4. Checking Python dependencies..."
if ! python3 -c "import pulumi; import pulumi_aws" 2>/dev/null; then
    echo "❌ Pulumi Python packages not installed. Run:"
    echo "   cd infrastructure"
    echo "   uv pip install -e '.[dev]'"
    exit 1
fi
echo "✅ Python dependencies installed"
echo ""

echo "5. Checking Pulumi stacks..."
STACKS=$(pulumi stack ls 2>&1 | grep -v "NAME" | awk '{print $1}' || echo "")
if [ -z "$STACKS" ]; then
    echo "⚠️  No stacks found. You need to create a stack first:"
    echo ""
    echo "   For test environment:"
    echo "   pulumi stack init test"
    echo "   pulumi config set aws:region us-east-1"
    echo "   pulumi config set s3BucketName pulumi-provisioning-test-bucket"
    echo "   pulumi config set dbName pulumi_test_db"
    echo "   pulumi config set --secret dbPassword <your-password>"
    echo ""
    echo "   Then run this script again."
    exit 1
fi
echo "✅ Stacks found:"
echo "$STACKS" | while read stack; do
    echo "   - $stack"
done
echo ""

echo "6. Selecting stack (using first available or 'test' if exists)..."
if echo "$STACKS" | grep -q "test"; then
    SELECTED_STACK="test"
else
    SELECTED_STACK=$(echo "$STACKS" | head -1 | awk '{print $1}')
fi

if [ -n "$SELECTED_STACK" ]; then
    pulumi stack select "$SELECTED_STACK" 2>/dev/null || true
    echo "✅ Selected stack: $SELECTED_STACK"
else
    echo "❌ No stack selected"
    exit 1
fi
echo ""

echo "7. Running Pulumi Preview (dry-run - no changes will be made)..."
echo "   This shows what resources will be created/updated/deleted"
echo "   ============================================================="
echo ""

pulumi preview --stack "$SELECTED_STACK" || {
    echo ""
    echo "❌ Preview failed. Check the errors above."
    echo ""
    echo "Common issues:"
    echo "  - Missing configuration: pulumi config set <key> <value>"
    echo "  - Missing secrets: pulumi config set --secret <key> <value>"
    echo "  - AWS permissions: Check IAM policies"
    exit 1
}

echo ""
echo "============================================================="
echo "✅ Preview completed successfully!"
echo ""
echo "Next steps:"
echo "  - Review the changes above"
echo "  - If everything looks good, deploy with: pulumi up"
echo "  - To see detailed diff: pulumi preview --diff"
echo ""

