#!/bin/bash
# Script to get GitHub's OIDC provider thumbprint
# This thumbprint is used when creating the OIDC identity provider in AWS

echo "Getting GitHub OIDC provider thumbprint..."
echo ""

# GitHub's OIDC provider URL
GITHUB_OIDC_URL="token.actions.githubusercontent.com"

# Method 1: Using openssl (most reliable)
echo "Method 1: Using openssl"
THUMBPRINT=$(echo | openssl s_client -servername ${GITHUB_OIDC_URL} -showcerts -connect ${GITHUB_OIDC_URL}:443 2>/dev/null | \
  openssl x509 -fingerprint -noout -sha1 | \
  sed 's/://g' | \
  cut -d'=' -f2 | \
  tr '[:upper:]' '[:lower:]')

if [ -n "$THUMBPRINT" ]; then
  echo "✅ Thumbprint: $THUMBPRINT"
else
  echo "❌ Failed to get thumbprint using openssl"
fi

echo ""
echo "Method 2: Using curl and openssl"
THUMBPRINT2=$(curl -s "https://${GITHUB_OIDC_URL}/.well-known/openid-configuration" > /dev/null 2>&1 && \
  echo | openssl s_client -servername ${GITHUB_OIDC_URL} -connect ${GITHUB_OIDC_URL}:443 2>/dev/null | \
  openssl x509 -fingerprint -noout -sha1 | \
  sed 's/://g' | \
  cut -d'=' -f2 | \
  tr '[:upper:]' '[:lower:]')

if [ -n "$THUMBPRINT2" ]; then
  echo "✅ Thumbprint: $THUMBPRINT2"
else
  echo "❌ Failed to get thumbprint using curl+openssl"
fi

echo ""
echo "=== Current GitHub Thumbprint (as of 2024) ==="
echo "6938fd4d98bab03faadb97b34396831e3780aea1"
echo ""
echo "Note: If the thumbprints above don't match, GitHub may have rotated certificates."
echo "Use the thumbprint from Method 1 or 2 above when creating the OIDC provider."

