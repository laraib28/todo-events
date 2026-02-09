# Manual Testing Guide for Chat Endpoint

This guide provides manual test cases using curl to verify the chat endpoint functionality.

## Prerequisites

1. Backend server running on `http://localhost:8000`
2. Database initialized with tables
3. A registered user account
4. Valid JWT token from authentication

---

## Setup: Get Authentication Token

First, register a user and get an authentication token:

```bash
# 1. Register a new user
curl -X POST http://localhost:8000/api/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123",
    "name": "Test User"
  }'

# 2. Login to get JWT token
curl -X POST http://localhost:8000/api/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123"
  }' \
  -c cookies.txt

# The JWT token is stored in cookies.txt
# Or extract it manually:
TOKEN=$(curl -X POST http://localhost:8000/api/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "testpass123"}' \
  -c - | grep access_token | awk '{print $7}')
```

---

## Test Case 1: Successful Chat Request (No Tool Call)

**Test**: Send a greeting message (no task operation)

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -H "Cookie: access_token=${TOKEN}" \
  -d '{
    "message": "Hello"
  }' \
  -v
```

**Expected Response:**
```json
{
  "message": "Hello! I'm here to help you manage your todo tasks. You can ask me to create, update, complete, delete, or show tasks. What would you like to do?",
  "metadata": null
}
```

**Expected Status:** `200 OK`

---

## Test Case 2: Create Task (Task Creation Metadata)

**Test**: Create a new task with priority

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -H "Cookie: access_token=${TOKEN}" \
  -d '{
    "message": "Add buy milk with high priority"
  }' \
  -v
```

**Expected Response:**
```json
{
  "message": "I've created a new task: 'buy milk' with high priority.",
  "metadata": {
    "action": "task_created",
    "task_id": 1
  }
}
```

**Expected Status:** `200 OK`

---

## Test Case 3: List Tasks (Task Listing Metadata)

**Test**: List all tasks

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -H "Cookie: access_token=${TOKEN}" \
  -d '{
    "message": "Show my tasks"
  }' \
  -v
```

**Expected Response:**
```json
{
  "message": "You have 1 task:\n1. buy milk (ID: 1, Priority: high, Status: incomplete)",
  "metadata": {
    "action": "tasks_listed",
    "count": 1
  }
}
```

**Expected Status:** `200 OK`

---

## Test Case 4: Update Task

**Test**: Update an existing task

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -H "Cookie: access_token=${TOKEN}" \
  -d '{
    "message": "Change buy milk to buy almond milk"
  }' \
  -v
```

**Expected Response:**
```json
{
  "message": "I've updated the task to 'buy almond milk'.",
  "metadata": {
    "action": "task_updated",
    "task_id": 1
  }
}
```

**Expected Status:** `200 OK`

---

## Test Case 5: Complete Task

**Test**: Mark a task as complete

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -H "Cookie: access_token=${TOKEN}" \
  -d '{
    "message": "Mark buy almond milk as done"
  }' \
  -v
```

**Expected Response:**
```json
{
  "message": "I've marked 'buy almond milk' as complete.",
  "metadata": {
    "action": "task_completed",
    "task_id": 1
  }
}
```

**Expected Status:** `200 OK`

---

## Test Case 6: Delete Task

**Test**: Delete a task

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -H "Cookie: access_token=${TOKEN}" \
  -d '{
    "message": "Delete the buy almond milk task"
  }' \
  -v
```

**Expected Response:**
```json
{
  "message": "I've deleted the task 'buy almond milk'.",
  "metadata": {
    "action": "task_deleted",
    "task_id": 1
  }
}
```

**Expected Status:** `200 OK`

---

## Error Test Cases

### Test Case E1: No Authentication

**Test**: Request without JWT token

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello"
  }' \
  -v
```

**Expected Response:**
```json
{
  "detail": "Not authenticated"
}
```

**Expected Status:** `401 Unauthorized`

---

### Test Case E2: Invalid Token

**Test**: Request with invalid JWT token

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -H "Cookie: access_token=invalid.token.here" \
  -d '{
    "message": "Hello"
  }' \
  -v
```

**Expected Response:**
```json
{
  "detail": "Invalid token"
}
```

**Expected Status:** `401 Unauthorized`

---

### Test Case E3: Empty Message

**Test**: Request with empty message

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -H "Cookie: access_token=${TOKEN}" \
  -d '{
    "message": ""
  }' \
  -v
```

**Expected Response:**
```json
{
  "detail": [
    {
      "loc": ["body", "message"],
      "msg": "ensure this value has at least 1 characters",
      "type": "value_error.any_str.min_length"
    }
  ]
}
```

**Expected Status:** `422 Unprocessable Entity`

---

### Test Case E4: Whitespace Only Message

**Test**: Request with whitespace-only message

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -H "Cookie: access_token=${TOKEN}" \
  -d '{
    "message": "   "
  }' \
  -v
```

**Expected Response:**
```json
{
  "detail": [
    {
      "loc": ["body", "message"],
      "msg": "Message cannot be empty or whitespace only",
      "type": "value_error"
    }
  ]
}
```

**Expected Status:** `422 Unprocessable Entity`

---

### Test Case E5: Message Too Long

**Test**: Request with message > 2000 characters

```bash
# Generate a 2001 character message
LONG_MSG=$(python3 -c "print('a' * 2001)")

curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -H "Cookie: access_token=${TOKEN}" \
  -d "{
    \"message\": \"${LONG_MSG}\"
  }" \
  -v
```

**Expected Response:**
```json
{
  "detail": [
    {
      "loc": ["body", "message"],
      "msg": "ensure this value has at most 2000 characters",
      "type": "value_error.any_str.max_length"
    }
  ]
}
```

**Expected Status:** `422 Unprocessable Entity`

---

### Test Case E6: Missing Message Field

**Test**: Request without message field

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -H "Cookie: access_token=${TOKEN}" \
  -d '{}' \
  -v
```

**Expected Response:**
```json
{
  "detail": [
    {
      "loc": ["body", "message"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**Expected Status:** `422 Unprocessable Entity`

---

## Performance Tests

### Test Case P1: Response Time

**Test**: Measure end-to-end response time

```bash
time curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -H "Cookie: access_token=${TOKEN}" \
  -d '{
    "message": "Add test task"
  }' \
  -o /dev/null -s -w "Total time: %{time_total}s\n"
```

**Expected:** < 3 seconds (p95 latency requirement)

---

### Test Case P2: Concurrent Requests

**Test**: Send 10 concurrent requests

```bash
# Requires GNU parallel or xargs
seq 10 | parallel -j 10 "curl -X POST http://localhost:8000/api/chat \
  -H 'Content-Type: application/json' \
  -H 'Cookie: access_token=${TOKEN}' \
  -d '{\"message\": \"Hello {}\"}' \
  -s -o /dev/null -w 'Request {}: %{http_code} in %{time_total}s\n'"
```

**Expected:** All requests return 200, no timeouts

---

## Conversation History Tests

### Test Case C1: Multi-Turn Conversation

**Test**: Verify conversation context is maintained

```bash
# Turn 1: Create task
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -H "Cookie: access_token=${TOKEN}" \
  -d '{"message": "Add buy groceries"}' \
  -s | jq

# Turn 2: Update the task (uses context from turn 1)
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -H "Cookie: access_token=${TOKEN}" \
  -d '{"message": "Make it high priority"}' \
  -s | jq

# Turn 3: Complete it (uses context from turns 1-2)
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -H "Cookie: access_token=${TOKEN}" \
  -d '{"message": "Mark it as done"}' \
  -s | jq
```

**Expected:** AI should understand "it" refers to the "buy groceries" task

---

## Database Verification

After running tests, verify data in database:

```bash
# Connect to database
psql $DATABASE_URL

# Check conversation history
SELECT id, user_id, role, LEFT(content, 50) as content, created_at
FROM conversation_history
ORDER BY created_at DESC
LIMIT 10;

# Check created tasks
SELECT id, user_id, title, priority, is_complete, created_at
FROM tasks
ORDER BY created_at DESC
LIMIT 10;
```

---

## Full Test Script

Save this as `test_chat.sh`:

```bash
#!/bin/bash

# Chat endpoint test script

# Configuration
API_URL="http://localhost:8000/api"
EMAIL="test@example.com"
PASSWORD="testpass123"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Register user (ignore if already exists)
echo "Registering user..."
curl -X POST ${API_URL}/register \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"${EMAIL}\", \"password\": \"${PASSWORD}\", \"name\": \"Test User\"}" \
  -s > /dev/null

# Login and get token
echo "Logging in..."
TOKEN=$(curl -X POST ${API_URL}/login \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"${EMAIL}\", \"password\": \"${PASSWORD}\"}" \
  -c - -s | grep access_token | awk '{print $7}')

if [ -z "$TOKEN" ]; then
    echo -e "${RED}Failed to get authentication token${NC}"
    exit 1
fi

echo -e "${GREEN}Authentication successful${NC}"

# Test 1: Simple greeting
echo -e "\nTest 1: Simple greeting"
RESPONSE=$(curl -X POST ${API_URL}/chat \
  -H "Content-Type: application/json" \
  -H "Cookie: access_token=${TOKEN}" \
  -d '{"message": "Hello"}' \
  -s)
echo $RESPONSE | jq

# Test 2: Create task
echo -e "\nTest 2: Create task"
RESPONSE=$(curl -X POST ${API_URL}/chat \
  -H "Content-Type: application/json" \
  -H "Cookie: access_token=${TOKEN}" \
  -d '{"message": "Add buy milk with high priority"}' \
  -s)
echo $RESPONSE | jq

# Test 3: List tasks
echo -e "\nTest 3: List tasks"
RESPONSE=$(curl -X POST ${API_URL}/chat \
  -H "Content-Type: application/json" \
  -H "Cookie: access_token=${TOKEN}" \
  -d '{"message": "Show my tasks"}' \
  -s)
echo $RESPONSE | jq

# Test 4: Error - No auth
echo -e "\nTest 4: Error handling (no auth)"
RESPONSE=$(curl -X POST ${API_URL}/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello"}' \
  -s)
HTTP_CODE=$(curl -X POST ${API_URL}/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello"}' \
  -s -w "%{http_code}" -o /dev/null)
if [ "$HTTP_CODE" = "401" ]; then
    echo -e "${GREEN}✓ Authentication error handled correctly${NC}"
else
    echo -e "${RED}✗ Expected 401, got ${HTTP_CODE}${NC}"
fi

echo -e "\n${GREEN}All tests completed${NC}"
```

Make it executable and run:
```bash
chmod +x test_chat.sh
./test_chat.sh
```

---

## Notes

- Replace `${TOKEN}` with your actual JWT token
- Ensure backend server is running before testing
- Check backend logs for detailed error messages
- OpenAI API key must be valid for AI responses to work
- Use `-v` flag with curl for verbose output including headers
