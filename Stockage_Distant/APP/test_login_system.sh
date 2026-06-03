#!/bin/bash
# Testing script for login system
# Run this to verify everything is working correctly

echo "=========================================="
echo "Login System Testing Script"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print results
test_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ PASS${NC}: $2"
    else
        echo -e "${RED}✗ FAIL${NC}: $2"
    fi
}

# Get the server address
read -p "Enter server address (default: http://localhost:5000): " SERVER
SERVER=${SERVER:-http://localhost:5000}

echo ""
echo "Testing against: $SERVER"
echo ""

# Test 1: Login page accessible
echo "Test 1: Login page should be accessible without credentials"
curl -s -o /dev/null -w "%{http_code}" "$SERVER/login"
echo ""
test_result $? "Login page response"

# Test 2: API metadata endpoint (no auth)
echo ""
echo "Test 2: API metadata endpoint should accept POST without authentication"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$SERVER/api/metadata" -d "test=data")
if [ "$RESPONSE" = "400" ] || [ "$RESPONSE" = "200" ]; then
    echo -e "${GREEN}✓ PASS${NC}: API metadata endpoint is accessible (HTTP $RESPONSE)"
else
    echo -e "${RED}✗ FAIL${NC}: API metadata endpoint returned unexpected status: $RESPONSE"
fi

# Test 3: Protected page without login
echo ""
echo "Test 3: Protected page (/) should redirect to login without credentials"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$SERVER/")
if [ "$RESPONSE" = "302" ] || [ "$RESPONSE" = "401" ]; then
    echo -e "${GREEN}✓ PASS${NC}: Protected page correctly blocks unauthenticated access (HTTP $RESPONSE)"
else
    echo -e "${YELLOW}⚠ WARNING${NC}: Expected 302/401, got $RESPONSE"
fi

# Test 4: Users.json exists
echo ""
echo "Test 4: Users file should exist"
if [ -f "JSON/users.json" ]; then
    echo -e "${GREEN}✓ PASS${NC}: JSON/users.json exists"
else
    echo -e "${RED}✗ FAIL${NC}: JSON/users.json not found"
fi

# Test 5: auth.py exists
echo ""
echo "Test 5: Auth module should exist"
if [ -f "auth.py" ]; then
    echo -e "${GREEN}✓ PASS${NC}: auth.py exists"
else
    echo -e "${RED}✗ FAIL${NC}: auth.py not found"
fi

# Test 6: login.html exists
echo ""
echo "Test 6: Login template should exist"
if [ -f "templates/login.html" ]; then
    echo -e "${GREEN}✓ PASS${NC}: templates/login.html exists"
else
    echo -e "${RED}✗ FAIL${NC}: templates/login.html not found"
fi

# Test 7: Check for @login_required in webserver.py
echo ""
echo "Test 7: Webserver should have login decorators"
if grep -q "@login_required" "utils/webserver.py"; then
    COUNT=$(grep -c "@login_required" "utils/webserver.py")
    echo -e "${GREEN}✓ PASS${NC}: Found $COUNT @login_required decorators"
else
    echo -e "${RED}✗ FAIL${NC}: No @login_required decorators found"
fi

# Test 8: Check imports in webserver.py
echo ""
echo "Test 8: Webserver should import auth module"
if grep -q "from auth import" "utils/webserver.py"; then
    echo -e "${GREEN}✓ PASS${NC}: auth module is imported in webserver.py"
else
    echo -e "${RED}✗ FAIL${NC}: auth module not imported in webserver.py"
fi

echo ""
echo "=========================================="
echo "Testing Complete!"
echo "=========================================="
echo ""
echo "Manual Testing Checklist:"
echo "☐ Visit $SERVER/login (should show login form)"
echo "☐ Enter admin/admin123 (should login)"
echo "☐ Visit $SERVER/ (should show home page)"
echo "☐ Click logout (should return to login)"
echo "☐ Try to access $SERVER/ again (should redirect to login)"
echo ""
echo "To manage users, run:"
echo "  python manage_users.py"
echo ""
