#!/bin/bash
# Session startup hook for Claude Code on the web
set -euo pipefail

# Only run in remote Claude Code environment
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
    exit 0
fi

echo "Setting up development environment..."

pip install -e "$CLAUDE_PROJECT_DIR/ductus[proof,bench,test]"

echo "Session startup complete"
