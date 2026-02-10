#!/usr/bin/env bash
set -euo pipefail

# OSS boundary check
# Ensures that code under oss/ never imports from continuum_engine (core).
# See BOUNDARY.md for the full policy.

echo "Checking OSS boundary: oss/ must not import from continuum_engine..."

violations=0

# Check Python imports
if grep -rn "from continuum_engine" oss/ --include="*.py" 2>/dev/null; then
  echo "ERROR: Found 'from continuum_engine' imports in oss/"
  violations=$((violations + 1))
fi

if grep -rn "import continuum_engine" oss/ --include="*.py" 2>/dev/null; then
  echo "ERROR: Found 'import continuum_engine' imports in oss/"
  violations=$((violations + 1))
fi

# Check TypeScript imports (for future TS SDK)
if grep -rn "from ['\"]continuum-engine" oss/ --include="*.ts" --include="*.tsx" 2>/dev/null; then
  echo "ERROR: Found continuum-engine imports in oss/ TypeScript files"
  violations=$((violations + 1))
fi

if [ "$violations" -gt 0 ]; then
  echo ""
  echo "FAIL: OSS boundary violated. See BOUNDARY.md for rules."
  echo "  - oss/ (Apache-2.0) must NEVER import from continuum_engine/continuum-engine (BSL-1.1)"
  echo "  - Use abstract base classes in oss/sdk/python/src/continuum/hooks.py for extension points"
  exit 1
fi

echo "OK: No boundary violations found."
