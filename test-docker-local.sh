#!/bin/bash
# Script to build and test Docker image locally

set -e

echo "🐳 Building Docker image..."
docker build -t fastapi-app:local .

echo ""
echo "✅ Build complete! Testing if container starts..."
echo ""

# Test 1: Just start the container and see if it runs
echo "Test 1: Starting container (will stop after 10 seconds if successful)..."
timeout 10 docker run --rm \
  -e AWS_REGION=us-east-1 \
  -e S3_BUCKET_NAME=test-bucket \
  -e DB_HOST=localhost \
  -e DB_NAME=test_db \
  -e DB_USER=testuser \
  -e DB_PASSWORD=testpass \
  -p 8000:8000 \
  fastapi-app:local || true

echo ""
echo "Test 2: Starting container in background and checking health endpoint..."
CONTAINER_ID=$(docker run -d \
  -e AWS_REGION=us-east-1 \
  -e S3_BUCKET_NAME=test-bucket \
  -e DB_HOST=localhost \
  -e DB_NAME=test_db \
  -e DB_USER=testuser \
  -e DB_PASSWORD=testpass \
  -p 8000:8000 \
  fastapi-app:local)

echo "Container ID: $CONTAINER_ID"
echo "Waiting 5 seconds for app to start..."
sleep 5

echo ""
echo "Checking container logs:"
docker logs $CONTAINER_ID

echo ""
echo "Testing health endpoint:"
curl -s http://localhost:8000/health || echo "❌ Health check failed"

echo ""
echo "Cleaning up..."
docker stop $CONTAINER_ID
docker rm $CONTAINER_ID

echo ""
echo "✅ Local test complete!"

