#!/usr/bin/env bash
# Remove all learned templates and reset the registry to empty.
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)/learned_templates"

# Remove all .py files
count=$(find "$DIR" -maxdepth 1 -name "*.py" | wc -l | tr -d ' ')
if [ "$count" -gt 0 ]; then
  find "$DIR" -maxdepth 1 -name "*.py" -delete
  echo "Removed $count learned template file(s)."
else
  echo "No learned template files to remove."
fi

# Reset registry
cat > "$DIR/registry.json" <<'EOF'
{
  "version": 1,
  "templates": {}
}
EOF
echo "Registry reset."
