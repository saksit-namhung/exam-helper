#!/bin/bash
# Test the app locally with Docker
# Usage: ./test-local.sh

set -e

echo "=== Testing Exam Helper Locally with Docker ==="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running"
    echo "Please start Docker Desktop and try again"
    exit 1
fi

echo "Step 1: Building Docker image..."
docker build -t exam-helper:local .

echo ""
echo "Step 2: Starting container on port 8080..."
echo ""

# Stop any existing container
docker stop exam-helper-local 2>/dev/null || true
docker rm exam-helper-local 2>/dev/null || true

# Run the container
docker run -d \
  --name exam-helper-local \
  -p 8080:8080 \
  -e PORT=8080 \
  exam-helper:local

echo "Container started!"
echo ""
echo "Waiting for app to start..."
sleep 3

# Test the app
echo "Testing API endpoints..."
echo ""

# Test health
if curl -s http://localhost:8080/ > /dev/null; then
    echo "✓ Main page accessible"
else
    echo "✗ Main page failed"
fi

# Test exams API
if curl -s http://localhost:8080/api/exams | grep -q "exam"; then
    echo "✓ API endpoint working"
    echo ""
    echo "Available exams:"
    curl -s http://localhost:8080/api/exams | python3 -m json.tool
else
    echo "✗ API endpoint failed"
fi

echo ""
echo "=== App is running at http://localhost:8080 ==="
echo ""
echo "To view logs:"
echo "  docker logs -f exam-helper-local"
echo ""
echo "To stop the container:"
echo "  docker stop exam-helper-local"
echo "  docker rm exam-helper-local"
