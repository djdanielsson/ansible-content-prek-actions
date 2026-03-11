#!/usr/bin/env bash
# WARNING: This hook can be slow. It builds an Ansible execution environment image.
set -euo pipefail

if ! command -v ansible-builder &>/dev/null; then
    echo "ERROR: ansible-builder is not installed."
    echo "Install it with: pip install ansible-builder"
    exit 1
fi

RUNTIME=""
if command -v podman &>/dev/null; then
    RUNTIME="podman"
elif command -v docker &>/dev/null; then
    RUNTIME="docker"
else
    echo "ERROR: Neither podman nor docker is installed."
    echo "Install one of them to build execution environments."
    exit 1
fi

if [[ ! -f execution-environment.yml ]]; then
    echo "ERROR: No execution-environment.yml found in the current directory."
    echo "This hook requires an execution-environment.yml to build."
    exit 1
fi

exec ansible-builder build -v 3 --container-runtime "${RUNTIME}" "$@"
