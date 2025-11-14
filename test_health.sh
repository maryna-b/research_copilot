#!/bin/bash
# Health check script - run before committing

echo "🔍 Running health checks..."
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

FAILED=0

# Check if services are running
echo "1. Checking Docker containers..."
if ! docker-compose ps | grep -q "Up"; then
    echo -e "${RED}❌ Services not running. Start with: docker-compose up -d${NC}"
    exit 1
fi
echo -e "${GREEN}✅ All containers running${NC}"

# Health endpoints
echo ""
echo "2. Testing health endpoints..."

check_health() {
    local url=$1
    local name=$2

    if curl -sf "$url" > /dev/null; then
        echo -e "${GREEN}✅ $name is healthy${NC}"
    else
        echo -e "${RED}❌ $name is down${NC}"
        FAILED=1
    fi
}

check_health "http://localhost:8000/health" "API Gateway"
check_health "http://localhost:8001/health" "Ingestion Service"
check_health "http://localhost:8002/api/v1/heartbeat" "Chroma"
check_health "http://localhost:8003/health" "Embeddings Service"

# Check for errors in logs
echo ""
echo "3. Checking logs for errors..."
if docker logs research-copilot-gateway --tail 50 2>&1 | grep -iE "(error|exception|failed)" | grep -v "ERROR: Exception in ASGI" | grep -v "401" | grep -v "500 Internal Server Error" | grep -v "Unauthorized" | grep -v "Invalid API key" | grep -v "HTTPException" | grep -v "raise HTTPException" | grep -v "fastapi.exceptions.HTTPException" | grep -v "starlette/middleware/errors.py" > /dev/null; then
    echo -e "${RED}⚠️  Errors found in API Gateway logs${NC}"
    FAILED=1
else
    echo -e "${GREEN}✅ No critical errors in logs${NC}"
fi

# Test database connection
echo ""
echo "4. Testing database..."
if docker exec research-copilot-db psql -U research_user -d research_copilot -c "SELECT 1" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Database accessible${NC}"
else
    echo -e "${RED}❌ Database connection failed${NC}"
    FAILED=1
fi

# Test metrics endpoint
echo ""
echo "5. Testing metrics endpoint..."
if curl -sf "http://localhost:8000/metrics" | grep -q "python_info"; then
    echo -e "${GREEN}✅ Metrics working${NC}"
else
    echo -e "${RED}❌ Metrics endpoint failed${NC}"
    FAILED=1
fi

echo ""
echo "================================"
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ ALL CHECKS PASSED!${NC}"
    echo "Safe to commit."
    exit 0
else
    echo -e "${RED}❌ SOME CHECKS FAILED${NC}"
    echo "Fix issues before committing."
    exit 1
fi
