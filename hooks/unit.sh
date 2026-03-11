#!/usr/bin/env bash
# WARNING: This hook can be slow. It runs the full tox-ansible unit test suite.
set -euo pipefail

if ! python3 -m tox --version &>/dev/null; then
    echo "ERROR: tox is not installed."
    echo "Install it with: pip install tox-ansible"
    exit 1
fi

if ! python3 -c "import tox_ansible" &>/dev/null; then
    echo "ERROR: tox-ansible is not installed."
    echo "Install it with: pip install tox-ansible"
    exit 1
fi

CREATED_DEFAULT=0
if [[ ! -f tox-ansible.ini ]]; then
    echo "INFO: No tox-ansible.ini found, creating default..."
    cat > tox-ansible.ini <<'TOX_EOF'
[ansible]
skip =
    py3.7
    py3.8
    2.9
    2.10
    2.11
    2.12
    2.13
TOX_EOF
    CREATED_DEFAULT=1
fi

cleanup() {
    if [[ "${CREATED_DEFAULT}" == "1" ]]; then
        rm -f tox-ansible.ini
    fi
}
trap cleanup EXIT

ENVS=$(python3 -m tox --ansible --conf tox-ansible.ini -l 2>/dev/null | grep "^unit-" | paste -sd, - || true)
if [[ -z "$ENVS" ]]; then
    echo "No unit test environments found."
    exit 0
fi

exec python3 -m tox --ansible --conf tox-ansible.ini -e "$ENVS" "$@"
