# ansible-content-prek-actions

Pre-commit / [prek](https://github.com/j178/prek) hooks for testing Ansible collection repositories locally, mirroring the CI checks provided by [ansible-content-actions](https://github.com/ansible/ansible-content-actions).

## Available Hooks

| Hook ID | Description | Pinned Dependencies | Speed |
| --- | --- | --- | --- |
| `ansible-lint` | Run ansible-lint on the collection | `ansible-lint==26.3.0` | Fast |
| `changelog` | Validate changelog fragments exist and are formatted correctly | `pyyaml==6.0.2` | Fast |
| `build-import` | Build the collection tarball and run galaxy-importer | `ansible-core==2.18.14`, `galaxy-importer==0.4.37` | Medium |
| `sanity` | Run tox-ansible sanity tests | `tox-ansible==26.3.0` | **Slow** |
| `unit` | Run tox-ansible unit tests | `tox-ansible==26.3.0` | **Slow** |
| `integration` | Run tox-ansible integration tests | `tox-ansible==26.3.0` | **Slow** |
| `ee-build` | Build an execution environment image | `ansible-builder==3.1.0` | **Slow** |

> **Note:** Hooks marked **Slow** default to `stages: [manual]` and will not run
> on every commit. See [Running slow hooks](#running-slow-hooks) below.

All hooks use `language: python`, which means pre-commit/prek automatically
creates an **isolated virtual environment** per hook and installs the pinned
dependencies. No manual `pip install` is required.

## Quick Start

Install [prek](https://prek.j178.dev/) (or [pre-commit](https://pre-commit.com/)):

```bash
# prek (recommended)
pip install prek

# or pre-commit
pip install pre-commit
```

Add to your collection's `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/djdanielsson/ansible-content-prek-actions
    rev: v0.1.0
    hooks:
      - id: ansible-lint
      - id: changelog
      - id: build-import
```

Install the git hooks:

```bash
# prek
prek install

# or pre-commit
pre-commit install
```

That's it -- dependencies are installed automatically into isolated environments.

## Full Configuration

### `.pre-commit-config.yaml`

```yaml
repos:
  - repo: https://github.com/djdanielsson/ansible-content-prek-actions
    rev: v0.1.0
    hooks:
      # Fast hooks -- run on every commit
      - id: ansible-lint
      - id: changelog
      - id: build-import

      # Slow hooks -- manual stage by default
      # Include them to make them available via manual invocation
      - id: sanity
      - id: unit
      - id: integration
      - id: ee-build
```

### `prek.toml`

```toml
[[repos]]
repo = "https://github.com/djdanielsson/ansible-content-prek-actions"
rev = "v0.1.0"
hooks = [
  # Fast hooks -- run on every commit
  { id = "ansible-lint" },
  { id = "changelog" },
  { id = "build-import" },

  # Slow hooks -- manual stage by default
  { id = "sanity" },
  { id = "unit" },
  { id = "integration" },
  { id = "ee-build" },
]
```

## Overriding Dependency Versions

Each hook ships with pinned dependency versions for reproducibility. To override
a version (e.g. to match your project's ansible-core), use
`additional_dependencies` in your config:

```yaml
hooks:
  - id: build-import
    additional_dependencies:
      - ansible-core==2.17.8
      - galaxy-importer==0.4.37
```

## Running Slow Hooks

Hooks marked **Slow** (`sanity`, `unit`, `integration`, `ee-build`) are configured
with `stages: [manual]` by default so they never run automatically on commit. You
can invoke them explicitly:

```bash
# Run all manual-stage hooks
prek run --hook-stage manual

# Run a specific slow hook
prek run --hook-stage manual sanity

# With pre-commit
pre-commit run --hook-stage manual sanity
```

To make a slow hook run automatically (e.g., before push), override its stage in
your config:

```yaml
hooks:
  - id: sanity
    stages: [pre-push]
  - id: unit
    stages: [pre-push]
```

If you override stages to `[pre-commit]`, install the pre-push hook type as well:

```bash
prek install --hook-type pre-push
```

## Hook Details

### ansible-lint

Runs [ansible-lint](https://ansible.readthedocs.io/projects/lint/) against
the collection. Any arguments passed via `args:` are forwarded directly.

Pinned: `ansible-lint==26.3.0`

### changelog

Validates that changelog fragments under `changelogs/fragments/` exist and are
properly formatted. Compares against `origin/main` by default. Override the
base ref:

```yaml
hooks:
  - id: changelog
    args: [--ref, develop]
```

Pinned: `pyyaml==6.0.2`

### build-import

Builds the Ansible collection tarball and runs
[galaxy-importer](https://github.com/ansible/galaxy-importer) validation on it.

Pinned: `ansible-core==2.18.14`, `galaxy-importer==0.4.37`

### sanity

Runs the `tox-ansible` sanity test matrix. If no `tox-ansible.ini` is found in
the collection root, a sensible default is created automatically.

Pinned: `tox-ansible==26.3.0`

### unit

Runs the `tox-ansible` unit test matrix. Same `tox-ansible.ini` behavior as sanity.

Pinned: `tox-ansible==26.3.0`

### integration

Runs the `tox-ansible` integration test matrix. Same `tox-ansible.ini` behavior
as sanity.

Pinned: `tox-ansible==26.3.0`

### ee-build

Builds an Ansible execution environment using
[ansible-builder](https://ansible.readthedocs.io/projects/builder/). Requires
an `execution-environment.yml` in the collection root and either `podman` or
`docker` installed.

Pinned: `ansible-builder==3.1.0`

## Licensing

ansible-content-prek-actions is released under the Apache License version 2.0.
See the [LICENSE](LICENSE) file for details.

The `validate_changelog.py` script is adapted from
[ansible/ansible-content-actions](https://github.com/ansible/ansible-content-actions)
(Apache-2.0).
