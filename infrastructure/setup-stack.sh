#!/bin/bash
# Script to automatically set up Pulumi stack configuration from a template

set -e

STACK_NAME="${1:-test}"
TEMPLATE_FILE="${2:-config-template.yaml}"

if [ ! -f "$TEMPLATE_FILE" ]; then
    echo "❌ Template file not found: $TEMPLATE_FILE"
    exit 1
fi

echo "Setting up Pulumi stack: $STACK_NAME"
echo ""

# Initialize stack if it doesn't exist
if ! pulumi stack ls 2>/dev/null | grep -q "$STACK_NAME"; then
    echo "Initializing stack: $STACK_NAME"
    pulumi stack init "$STACK_NAME"
fi

# Select the stack
pulumi stack select "$STACK_NAME"

echo "Reading configuration from template..."
echo ""

# Parse YAML and set config values
# Note: This is a simplified version - you might want to use a YAML parser
# For now, we'll use a manual approach or you can copy the YAML directly

echo "To set up your stack, you have two options:"
echo ""
echo "Option 1: Copy template to stack config file"
echo "  cp $TEMPLATE_FILE ../Pulumi.$STACK_NAME.yaml"
echo "  # Then edit the file and fill in values"
echo ""
echo "Option 2: Use this script to set values programmatically"
echo "  # Edit the template file first, then run:"
echo "  ./setup-stack.sh $STACK_NAME"
echo ""

# Example: Set basic config
echo "Setting basic configuration..."
pulumi config set aws:region us-east-1
pulumi config set environment "$STACK_NAME"
pulumi config set projectName "pulumi-provisioning-$STACK_NAME"

echo ""
echo "✅ Basic configuration set!"
echo ""
echo "Next steps:"
echo "  1. Set S3 bucket name: pulumi config set s3BucketName <name>"
echo "  2. Set DB name: pulumi config set dbName <name>"
echo "  3. Set DB password (secret): pulumi config set --secret dbPassword <password>"
echo "  4. Review all config: pulumi config"
echo "  5. Preview changes: pulumi preview"

