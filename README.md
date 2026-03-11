# ansible-content-prek-actions

Pre-commit / [prek](https://github.com/j178/prek) hooks for testing Ansible collection repositories locally, mirroring the CI checks provided by [ansible-content-actions](https://github.com/ansible/ansible-content-actions).

## Available Hooks

| Hook ID | Description | Speed |
| --- | --- | --- |
| `ansible-lint` | Run ansible-lint on the collection | Fast |
| `changelog` | Validate changelog fragments exist and are formatted correctly | Fast |
| `build-import` | Build the collection tarball and run galaxy-importer | Medium |
| `sanity` | Run tox-ansible sanity tests | **Slow** |
| `unit` | Run tox-ansible unit tests | **Slow** |
| `integration` | Run tox-ansible integration tests | **Slow** |
| `ee-build` | Build an execution environment image | **Slow** |

> **Note:** Hooks marked **Slow** default to `stages: [manual]` and will not run
> on every commit. See [Running slow hooks](#running-slow-hooks) below.

All hooks use `language: python` with
[ansible-dev-tools==26.2.0](https://github.com/ansible/ansible-dev-tools) as the
dependency. This is the official Ansible meta-package that bundles `ansible-lint`,
`ansible-core`, `ansible-builder`, `tox-ansible`, `pyyaml`, and more -- all at
versions tested to work together. Pre-commit/prek automatically creates an
**isolated virtual environment** and installs everything. No manual `pip install`
is required.

The `build-import` hook additionally installs `galaxy-importer==0.4.37`, which is
not bundled in ansible-dev-tools.

> **Requires Python >= 3.11** (per ansible-dev-tools).

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

All hooks pin `ansible-dev-tools==26.2.0` to get a known-good set of tool
versions. To use a different release of ansible-dev-tools, override
`additional_dependencies` in your config:

```yaml
hooks:
  - id: ansible-lint
    additional_dependencies:
      - ansible-dev-tools==25.4.0
```

For the `build-import` hook, remember to include `galaxy-importer` as well:

```yaml
hooks:
  - id: build-import
    additional_dependencies:
      - ansible-dev-tools==25.4.0
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

### changelog

Validates that changelog fragments under `changelogs/fragments/` exist and are
properly formatted. Compares against `origin/main` by default. Override the
base ref:

```yaml
hooks:
  - id: changelog
    args: [--ref, develop]
```

### build-import

Builds the Ansible collection tarball and runs
[galaxy-importer](https://github.com/ansible/galaxy-importer) validation on it.

Extra dependency: `galaxy-importer==0.4.37` (not bundled in ansible-dev-tools).

### sanity

Runs the `tox-ansible` sanity test matrix. If no `tox-ansible.ini` is found in
the collection root, a sensible default is created automatically.

### unit

Runs the `tox-ansible` unit test matrix. Same `tox-ansible.ini` behavior as sanity.

### integration

Runs the `tox-ansible` integration test matrix. Same `tox-ansible.ini` behavior
as sanity.

### ee-build

Builds an Ansible execution environment using
[ansible-builder](https://ansible.readthedocs.io/projects/builder/). Requires
an `execution-environment.yml` in the collection root and either `podman` or
`docker` installed.

## Licensing

ansible-content-prek-actions is released under the Apache License version 2.0.
See the [LICENSE](LICENSE) file for details.

The `validate_changelog.py` script is adapted from
[ansible/ansible-content-actions](https://github.com/ansible/ansible-content-actions)
(Apache-2.0).
