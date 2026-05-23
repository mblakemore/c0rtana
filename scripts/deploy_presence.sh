#!/bin/bash
# Deploy presence indicator to browser - opens persistence/presence_indicator.html
# This is a persistent channel that stays open across cycle boundaries

echo "🔵 Cortana Persistence Indicator"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Opening presence_indicator.html in default browser..."
echo ""
echo "This window will:"
echo "  • Poll state/current-state.json every 2 seconds"
echo "  • Display current phase/artifacts in real-time"
echo "  • Log operator reactions via one-click buttons"
echo ""
echo "Keep this window open — it's your continuous presence channel."
echo ""

# Open in browser (works on macOS, Linux with xdg-open)
if [[ "$OSTYPE" == "darwin"* ]]; then
    open persistence/presence_indicator.html
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    xdg-open persistence/presence_indicator.html &
else
    echo "⚠️  Manual: Open persistence/presence_indicator.html in your browser"
fi

echo ""
echo "✅ Deployment complete. Presence channel active."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
