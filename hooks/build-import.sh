#!/usr/bin/env bash
set -euo pipefail

MISSING=()
if ! python3 -c "import ansible" &>/dev/null; then
    MISSING+=("ansible-core")
fi
if ! python3 -c "import galaxy_importer" &>/dev/null; then
    MISSING+=("galaxy-importer")
fi

if [[ ${#MISSING[@]} -gt 0 ]]; then
    echo "ERROR: Missing required packages: ${MISSING[*]}"
    echo "Install them with: pip install ${MISSING[*]}"
    exit 1
fi

TMPDIR="$(mktemp -d)"
trap 'rm -rf "${TMPDIR}"' EXIT

exec python3 -m galaxy_importer.main --git-clone-path . --output-path "${TMPDIR}"
