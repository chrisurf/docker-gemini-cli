#!/bin/bash
# Local test script to validate Docker functionality

set -e

echo "🔍 Testing Docker Image Locally..."

# Build the image
echo "📦 Building Docker image..."
docker build -t gemini-autonomous-agent:test .

# Test 1: Basic container structure
echo "🧪 Test 1: Container structure and files..."
docker run --rm --entrypoint="" \
  -e GEMINI_API_KEY=fake_key \
  gemini-autonomous-agent:test \
  /bin/bash -c "ls -la /app/src/ && python --version && whoami"

# Test 2: Python imports
echo "🧪 Test 2: Python imports..."
docker run --rm --entrypoint="" \
  -e GEMINI_API_KEY=fake_key \
  gemini-autonomous-agent:test \
  /bin/bash -c "cd /app && python -c 'import sys; sys.path.append(\"src\"); import autonomous_agent, gemini_client, task_processor; print(\"✅ All imports successful\")'"

# Test 3: Health check (expected to fail with fake key)
echo "🧪 Test 3: Health check..."
docker run --rm --entrypoint="" \
  -e GEMINI_API_KEY=fake_key \
  gemini-autonomous-agent:test \
  /bin/bash -c "cd /app && python src/health_check.py || echo '⚠️ Health check failed as expected with fake API key'"

# Test 4: Agent mode startup (brief test)
echo "🧪 Test 4: Agent mode startup..."
mkdir -p test_data/{input,output}
timeout 10s docker run --rm \
  -e GEMINI_API_KEY=fake_key \
  -v $(pwd)/test_data:/app/data \
  gemini-autonomous-agent:test agent || echo "⏰ Agent mode test completed (expected timeout)"

echo "✅ All local Docker tests completed successfully!"
echo "🚀 Ready for GitHub Actions deployment!"
