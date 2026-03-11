#!/usr/bin/env bash
set -euo pipefail

if ! python3 -c "import yaml" &>/dev/null; then
    echo "ERROR: pyyaml is not installed."
    echo "Install it with: pip install pyyaml"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

REF="main"
while [[ $# -gt 0 ]]; do
    case "$1" in
        --ref)
            REF="$2"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

exec python3 "${SCRIPT_DIR}/validate_changelog.py" --ref "${REF}"
