#!/bin/bash
###############################################################################
# ASTRA Autonomous Discovery Startup - Direct Python Version
#
# This script starts ASTRA using the correct Python interpreter where
# dependencies are installed. No manual intervention required.
#
# Usage: ./start_autonomous_direct.sh
###############################################################################

# Use the Python interpreter where dependencies are installed
PYTHON="/Library/Frameworks/Python.framework/Versions/3.14/bin/python3"

# Check if Python exists
if [ ! -f "$PYTHON" ]; then
    echo "❌ Python not found at: $PYTHON"
    echo "Please install dependencies first:"
    echo "  uv pip install --system arxiv sentence-transformers scikit-learn numpy scipy"
    exit 1
fi

# Check if dependencies are available
echo "Checking dependencies..."
if $PYTHON -c "import arxiv, sentence_transformers" 2>/dev/null; then
    echo "✅ All dependencies available"
else
    echo "❌ Dependencies missing - installing..."
    uv pip install --system arxiv sentence-transformers scikit-learn numpy scipy
fi

# Start the autonomous discovery system
echo "🚀 Starting ASTRA Autonomous Discovery System..."
echo "Using Python: $PYTHON"
echo "Press Ctrl+C to stop"
echo ""

# Run the system
exec $PYTHON start_autonomous_discovery.py