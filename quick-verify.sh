#!/bin/bash
echo "=========================================="
echo "  Quick Setup Verification"
echo "=========================================="
echo ""

# Check AWS
echo "1. AWS Configuration:"
if aws sts get-caller-identity &> /dev/null; then
    echo "   ✅ AWS credentials configured"
    aws sts get-caller-identity | grep -E "(Account|Arn)" | sed 's/^/   /'
else
    echo "   ❌ AWS credentials NOT configured"
    echo "   Run: aws configure --profile pulumi-dev"
fi
echo ""

# Check Profile
echo "2. Current AWS Profile:"
if [ -z "$AWS_PROFILE" ]; then
    echo "   ⚠️  No profile set (using default)"
    echo "   To set: export AWS_PROFILE=pulumi-dev"
else
    echo "   ✅ Profile: $AWS_PROFILE"
fi
echo ""

# Check Pulumi
echo "3. Pulumi Status:"
if pulumi whoami &> /dev/null; then
    echo "   ✅ Pulumi logged in: $(pulumi whoami)"
else
    echo "   ❌ Pulumi NOT logged in"
    echo "   Run: pulumi login"
fi
echo ""

echo "=========================================="
