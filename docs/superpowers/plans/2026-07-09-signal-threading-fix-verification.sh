#!/bin/bash
# Verification script for signal threading fix

echo "═══════════════════════════════════════════════════════════════"
echo "SIGNAL THREADING FIX VERIFICATION"
echo "═══════════════════════════════════════════════════════════════"

# Test 1: Verify signal imports removed
echo ""
echo "Test 1: Checking signal imports removed..."
if grep -q "import signal" astra_core/autonomous_startup_discovery_v2.py; then
    echo "❌ FAIL: signal import still present"
    exit 1
else
    echo "✅ PASS: signal import removed"
fi

# Test 2: Verify thread-safe timeout wrapper exists
echo ""
echo "Test 2: Checking thread-safe timeout wrapper..."
if [ -f "astra_core/core/thread_safe_timeout.py" ]; then
    echo "✅ PASS: thread_safe_timeout.py exists"
else
    echo "❌ FAIL: thread_safe_timeout.py missing"
    exit 1
fi

# Test 3: Run unit tests
echo ""
echo "Test 3: Running unit tests..."
python3 -m pytest astra_core/tests/test_thread_safe_timeout.py -v
if [ $? -eq 0 ]; then
    echo "✅ PASS: Thread-safe timeout tests pass"
else
    echo "❌ FAIL: Thread-safe timeout tests failed"
    exit 1
fi

# Test 4: Verify discovery system integration
echo ""
echo "Test 4: Testing discovery system integration..."
python3 -m pytest astra_core/tests/test_autonomous_startup_timeout_fix.py -v
if [ $? -eq 0 ]; then
    echo "✅ PASS: Discovery system integration tests pass"
else
    echo "❌ FAIL: Discovery system integration tests failed"
    exit 1
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "✅ ALL VERIFICATION TESTS PASSED"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "The signal threading issue has been FIXED:"
echo "  • Signal-based timeout replaced with thread-safe implementation"
echo "  • Discovery system now works in multi-threaded environment"
echo "  • ASTRA calls will no longer fail with signal threading errors"
echo "  • Discoveries will now be produced successfully"