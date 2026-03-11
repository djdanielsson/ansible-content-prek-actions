#!/usr/bin/env bash
set -euo pipefail

if ! command -v ansible-lint &>/dev/null; then
    echo "ERROR: ansible-lint is not installed."
    echo "Install it with: pip install ansible-lint"
    exit 1
fi

exec ansible-lint "$@"
