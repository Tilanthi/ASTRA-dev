#!/bin/bash
# View full discoveries from 24/7 autonomous discovery

echo "=== AUTONOMOUS DISCOVERIES ==="
echo ""

LOG_FILE="$HOME/.astra_persistent/24_7_discovery.log"

if [ ! -f "$LOG_FILE" ]; then
    echo "❌ Discovery log not found. Start discovery first:"
    echo "   ./start_discovery.sh"
    exit 1
fi

# Extract and format discoveries
echo "Recent discoveries from $LOG_FILE:"
echo ""

grep "Discovery made:" "$LOG_FILE" | while IFS= read -r line; do
    # Extract timestamp and cycle
    TIMESTAMP=$(echo "$line" | grep -oP '\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}' | head -1)
    CYCLE=$(echo "$line" | grep -oP "'cycle': \K\d+")

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🔬 Discovery #$CYCLE"
    echo "📅 $(date -r "$(date -j -f "%Y-%m-%dT%H:%M:%S" "$TIMESTAMP" "+%s" 2>/dev/null || echo "$TIMESTAMP")" "+%Y-%m-%d %H:%M:%S" 2>/dev/null || echo "$TIMESTAMP")"

    # Try to extract the actual discovery content
    CONTENT=$(echo "$line" | grep -oP "'result': '\K[^']*" | sed 's/\\n/\n/g' | head -c 500)

    if [ -n "$CONTENT" ]; then
        echo ""
        echo "$CONTENT"
    else
        echo ""
        # Fallback: show raw line
        echo "$line" | sed -E 's/.*Discovery made: //' | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('result', data))" 2>/dev/null || echo "Content extraction failed"
    fi
    echo ""
done

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Total discoveries: $(grep -c "Discovery made:" "$LOG_FILE" 2>/dev/null || echo 0)"
echo ""
echo "View logs: tail -f ~/.astra_persistent/24_7_discovery.log"