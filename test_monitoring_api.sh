#!/bin/bash
# Test script for Comment Monitoring API
# Usage: ./test_monitoring_api.sh <TOKEN>

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Config
BASE_URL="http://localhost:8000"
TOKEN="${1:-YOUR_TOKEN_HERE}"

if [ "$TOKEN" = "YOUR_TOKEN_HERE" ]; then
    echo -e "${RED}❌ Please provide a JWT token as argument${NC}"
    echo "Usage: $0 <TOKEN>"
    exit 1
fi

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Comment Monitoring API Test Suite${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Test 1: Sync Instagram Posts
echo -e "${GREEN}Test 1: Sync Instagram Posts${NC}"
echo -e "POST ${BASE_URL}/api/monitoring/sync\n"
curl -X POST "${BASE_URL}/api/monitoring/sync" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"limit": 20}' \
  -w "\n\n" -s | jq '.'

sleep 2

# Test 2: List All Monitored Posts
echo -e "\n${GREEN}Test 2: List All Monitored Posts${NC}"
echo -e "GET ${BASE_URL}/api/monitoring/posts\n"
curl -X GET "${BASE_URL}/api/monitoring/posts?limit=10" \
  -H "Authorization: Bearer ${TOKEN}" \
  -w "\n\n" -s | jq '.'

sleep 2

# Test 3: List Only Enabled Posts
echo -e "\n${GREEN}Test 3: List Only Enabled Posts${NC}"
echo -e "GET ${BASE_URL}/api/monitoring/posts?monitoring_enabled=true\n"
curl -X GET "${BASE_URL}/api/monitoring/posts?monitoring_enabled=true" \
  -H "Authorization: Bearer ${TOKEN}" \
  -w "\n\n" -s | jq '.'

sleep 2

# Test 4: Get Monitoring Rules
echo -e "\n${GREEN}Test 4: Get Monitoring Rules${NC}"
echo -e "GET ${BASE_URL}/api/monitoring/rules\n"
curl -X GET "${BASE_URL}/api/monitoring/rules" \
  -H "Authorization: Bearer ${TOKEN}" \
  -w "\n\n" -s | jq '.'

sleep 2

# Test 5: Update Monitoring Rules
echo -e "\n${GREEN}Test 5: Update Monitoring Rules${NC}"
echo -e "PUT ${BASE_URL}/api/monitoring/rules\n"
curl -X PUT "${BASE_URL}/api/monitoring/rules" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "auto_monitor_enabled": true,
    "auto_monitor_count": 10,
    "monitoring_duration_days": 14
  }' \
  -w "\n\n" -s | jq '.'

sleep 2

# Test 6: Get a Post ID for Toggle Test
echo -e "\n${GREEN}Test 6: Get Post ID for Toggle Test${NC}"
POST_ID=$(curl -X GET "${BASE_URL}/api/monitoring/posts?limit=1" \
  -H "Authorization: Bearer ${TOKEN}" \
  -s | jq -r '.posts[0].id')

if [ "$POST_ID" != "null" ] && [ -n "$POST_ID" ]; then
    echo -e "Found post ID: ${POST_ID}\n"

    # Test 7: Toggle Monitoring (Disable)
    echo -e "${GREEN}Test 7: Toggle Monitoring (Disable)${NC}"
    echo -e "PATCH ${BASE_URL}/api/monitoring/posts/${POST_ID}/toggle\n"
    curl -X PATCH "${BASE_URL}/api/monitoring/posts/${POST_ID}/toggle" \
      -H "Authorization: Bearer ${TOKEN}" \
      -H "Content-Type: application/json" \
      -d '{}' \
      -w "\n\n" -s | jq '.'

    sleep 2

    # Test 8: Toggle Monitoring (Enable with custom duration)
    echo -e "\n${GREEN}Test 8: Toggle Monitoring (Enable)${NC}"
    echo -e "PATCH ${BASE_URL}/api/monitoring/posts/${POST_ID}/toggle\n"
    curl -X PATCH "${BASE_URL}/api/monitoring/posts/${POST_ID}/toggle" \
      -H "Authorization: Bearer ${TOKEN}" \
      -H "Content-Type: application/json" \
      -d '{"duration_days": 30}' \
      -w "\n\n" -s | jq '.'
else
    echo -e "${RED}❌ No posts found for toggle test${NC}\n"
fi

sleep 2

# Test 9: List Comments (existing endpoint, now with monitored_posts)
echo -e "\n${GREEN}Test 9: List Comments (with monitored_posts context)${NC}"
echo -e "GET ${BASE_URL}/api/comments?limit=5\n"
curl -X GET "${BASE_URL}/api/comments?limit=5" \
  -H "Authorization: Bearer ${TOKEN}" \
  -w "\n\n" -s | jq '.'

sleep 2

# Test 10: List Comments by Triage
echo -e "\n${GREEN}Test 10: List Comments Needing Response${NC}"
echo -e "GET ${BASE_URL}/api/comments?triage=respond\n"
curl -X GET "${BASE_URL}/api/comments?triage=respond&limit=5" \
  -H "Authorization: Bearer ${TOKEN}" \
  -w "\n\n" -s | jq '.'

echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}  All Tests Completed!${NC}"
echo -e "${BLUE}========================================${NC}\n"
