#!/bin/bash

echo "🧹 Killing Temporal servers and workers..."

# Kill by port (for servers)
if lsof -ti:7233 >/dev/null 2>&1; then
	echo "  Killing processes on port 7233 (Temporal server)..."
	lsof -ti:7233 | xargs kill -9 2>/dev/null
else
	echo "  ✓ No Temporal server found on port 7233"
fi

if lsof -ti:8233 >/dev/null 2>&1; then
	echo "  Killing processes on port 8233 (Temporal UI)..."
	lsof -ti:8233 | xargs kill -9 2>/dev/null
else
	echo "  ✓ No Temporal UI found on port 8233"
fi

# Kill by process name (more thorough)
if pgrep -f "investigate_worker" >/dev/null 2>&1; then
	echo "  Killing investigate_worker processes..."
	pkill -9 -f "investigate_worker" 2>/dev/null
else
	echo "  ✓ No investigate_worker processes found"
fi

if pgrep -f "temporal server start-dev" >/dev/null 2>&1; then
	echo "  Killing temporal server processes..."
	pkill -9 -f "temporal server start-dev" 2>/dev/null
else
	echo "  ✓ No temporal server processes found"
fi

if pgrep -f "uv run python -m investigate_worker" >/dev/null 2>&1; then
	echo "  Killing uv worker processes..."
	pkill -9 -f "uv run python -m investigate_worker" 2>/dev/null
else
	echo "  ✓ No uv worker processes found"
fi

# Give processes time to die
sleep 1

# Verify cleanup
remaining=$(ps aux | grep -E "investigate_worker|temporal server start-dev" | grep -v grep | wc -l | tr -d ' ')
if [[ "${remaining}" -eq 0 ]]; then
	echo ""
	echo "✅ Cleanup complete! All processes terminated."
else
	echo ""
	echo "⚠️  Warni$$${${${${${}}: $r}emai}ning process(es) may still be running"
	echo "Run 'ps aux | grep -E \"investigate_worker|temporal\"' to check"
fi
