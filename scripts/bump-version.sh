#!/usr/bin/env bash
set -euo pipefail

# Usage: ./scripts/bump-version.sh <package> <version>
#
# Examples:
#   ./scripts/bump-version.sh sdk 0.2.0
#   ./scripts/bump-version.sh cli 0.2.0
#   ./scripts/bump-version.sh mcp 0.2.0
#
# This script:
#   1. Updates the version in the package's pyproject.toml
#   2. Updates __init__.py __version__ if present (SDK only)
#   3. Creates a git tag: <package>-v<version>
#   4. Prints the tag for CI consumption

PACKAGE="${1:?Usage: bump-version.sh <sdk|cli|mcp> <version>}"
VERSION="${2:?Usage: bump-version.sh <sdk|cli|mcp> <version>}"

case "$PACKAGE" in
  sdk)
    PYPROJECT="oss/sdk/python/pyproject.toml"
    INIT_FILE="oss/sdk/python/src/continuum/__init__.py"
    TAG="sdk-v${VERSION}"
    ;;
  cli)
    PYPROJECT="oss/cli/pyproject.toml"
    INIT_FILE=""
    TAG="cli-v${VERSION}"
    ;;
  mcp)
    PYPROJECT="oss/mcp-server/pyproject.toml"
    INIT_FILE=""
    TAG="mcp-v${VERSION}"
    ;;
  *)
    echo "Unknown package: $PACKAGE (expected: sdk, cli, mcp)" >&2
    exit 1
    ;;
esac

# Update pyproject.toml version
if [[ ! -f "$PYPROJECT" ]]; then
  echo "Error: $PYPROJECT not found" >&2
  exit 1
fi

# Use sed to replace the version line
sed -i.bak "s/^version = \".*\"/version = \"${VERSION}\"/" "$PYPROJECT"
rm -f "${PYPROJECT}.bak"
echo "Updated $PYPROJECT -> ${VERSION}"

# Update __init__.py __version__ if applicable
if [[ -n "$INIT_FILE" && -f "$INIT_FILE" ]]; then
  sed -i.bak "s/^__version__ = \".*\"/__version__ = \"${VERSION}\"/" "$INIT_FILE"
  rm -f "${INIT_FILE}.bak"
  echo "Updated $INIT_FILE -> ${VERSION}"
fi

# Create git tag
echo ""
echo "To complete the release:"
echo "  git add $PYPROJECT${INIT_FILE:+ $INIT_FILE}"
echo "  git commit -m 'release: ${PACKAGE} v${VERSION}'"
echo "  git tag ${TAG}"
echo "  git push origin main ${TAG}"
echo ""
echo "Tag: ${TAG}"
