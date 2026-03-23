---
name: python-project-scaffold
description: >
  Full Python project bootstrapping workflow. Use this skill whenever the user wants to
  build a new Python tool, library, CLI, or module from scratch — especially when they
  mention "create X", "build X in Python", "write a Python project for X", or ask for
  a proper project with tests, linting, versioning, or git setup. Triggers on any
  request to scaffold, initialize, or structure a new Python project. Even if the user
  only says "build me X in Python", apply this skill — it encodes the full professional
  workflow: SPEC → implementation → pytest → README → lint → git. Always use this skill
  rather than improvising a one-off script when the deliverable is a reusable project.
---

# Python Project Scaffold Skill

Build a production-grade Python project from scratch, end-to-end. The workflow is
**strictly sequential**: spec first, code second, tests third, polish fourth, git last.
Never skip or reorder steps.

---

## Workflow

### Step 0 — Understand the Request

Before writing a single file, make sure you know:
- What the project does (purpose, inputs, outputs)
- Any constraints (pure stdlib? third-party ok? CLI or library?)
- Target Python version (default: 3.11+)

If the user's request is clear enough, proceed directly to Step 1. If ambiguous, ask
one focused clarifying question only.

---

### Step 1 — Write SPEC.md First

**Always write SPEC.md before writing any code.** No exceptions.

`SPEC.md` is the contract. Everything that follows must obey it.

```markdown
# SPEC.md — <ProjectName>

## Purpose
One paragraph: what this project does and why.

## Scope
- What IS in scope (explicit list)
- What is NOT in scope (explicit list)

## Public API / Interface
List every public function, class, CLI command, or module with:
- Signature (name, args, return type)
- Invariants and preconditions
- Error behavior

## Data Formats
Describe input/output data structures, file formats, encodings.

## Edge Cases
List at least 5 edge cases that the implementation must handle correctly.

## Performance & Constraints
Any O(n) requirements, memory limits, forbidden dependencies.

## Version
v0.1.0.1
```

After writing SPEC.md, **pause and verify it makes sense** before moving on.

---

### Step 2 — Project Structure

Create the following layout:

```
<project_name>/
├── SPEC.md
├── README.md
├── .gitignore
├── pyproject.toml          # PEP 517/518 build config + tool config
├── src/
│   └── <package_name>/
│       ├── __init__.py     # exports version + public API
│       └── <modules>.py
└── tests/
    ├── __init__.py
    ├── conftest.py         # shared fixtures
    └── test_<module>.py
```

**pyproject.toml minimum:**

```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.backends.legacy:build"

[project]
name = "<package_name>"
version = "0.1.0.1"
description = "<one-line description>"
requires-python = ">=3.11"
dependencies = []  # list real deps here

[tool.setuptools.packages.find]
where = ["src"]

[tool.black]
line-length = 88
target-version = ["py311"]

[tool.ruff]
line-length = 88
target-version = "py311"
select = ["E", "F", "W", "I", "UP"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --tb=short"
```

---

### Step 3 — Implementation

Follow SPEC.md **to the letter**. For each item in the spec's Public API:

- Implement it exactly as specced (name, signature, behavior)
- Add docstrings (one-line summary + Args/Returns/Raises)
- Handle all edge cases listed in SPEC.md
- Raise meaningful exceptions with descriptive messages

**`__init__.py` must export:**

```python
__version__ = "0.1.0.1"
__all__ = [...]  # every public symbol
```

Do not add features not in SPEC.md. If you realize the spec is wrong, update SPEC.md
first, then the code.

---

### Step 4 — Tests (pytest, heavy coverage)

Write tests **before assuming the implementation is correct**. Tests are the spec made
executable.

**Minimum test coverage requirements:**

| Category | Minimum |
|---|---|
| Happy path | 1 test per public function |
| Edge cases | Every edge case in SPEC.md gets a test |
| Error cases | Every documented exception gets a test |
| Boundary values | Empty input, single element, large input |
| Type correctness | Wrong-type args raise TypeError where appropriate |

**`conftest.py` pattern:**

```python
import pytest

@pytest.fixture
def sample_input():
    return ...  # reusable fixture for the most common test input
```

**Test naming convention:** `test_<function>_<scenario>`, e.g.:
- `test_parse_empty_string`
- `test_compute_large_n`
- `test_divide_by_zero_raises`

**Run tests and fix everything before moving on:**

```bash
cd <project_root>
pip install -e ".[dev]" --quiet
pytest -v
```

All tests must pass. Zero failures, zero errors.

---

### Step 5 — README.md

```markdown
# <ProjectName>

> One-line description.

## Install

```bash
pip install -e .
```

## Usage

```python
from <package_name> import <MainThing>
# minimal working example
```

## API

Brief description of each public symbol.

## Development

```bash
pip install -e ".[dev]"
pytest
black src/ tests/
ruff check src/ tests/
flake8 src/ tests/
```

## Version

v0.1.0.1
```

---

### Step 6 — .gitignore

```gitignore
__pycache__/
*.py[cod]
*.egg-info/
dist/
build/
.eggs/
*.egg
.env
.venv
venv/
env/
*.pyc
*.pyo
.pytest_cache/
.ruff_cache/
.mypy_cache/
htmlcov/
.coverage
*.log
.DS_Store
```

---

### Step 7 — Lint and Fix

Run all three linters in order and fix every warning. Do not skip any.

```bash
# Format first (black is the source of truth for style)
black src/ tests/

# Ruff: fast linter, catches unused imports, style, upgrades
ruff check src/ tests/ --fix

# Flake8: final pass, catches anything ruff missed
flake8 src/ tests/ --max-line-length=88 --extend-ignore=E203,W503
```

**Install dev deps if needed:**

```bash
pip install black ruff flake8 pytest --quiet
```

Fix ALL warnings. Do not suppress with `# noqa` unless there is a documented reason.
After fixing, re-run pytest to confirm nothing broke.

---

### Step 8 — Git Init, Commit, Push

```bash
cd <project_root>
git init
git add .
git commit -m "feat: initial release v0.1.0.1

- Implements <short description>
- Full pytest suite with <N> tests
- Linted with black, ruff, flake8"
```

**Push (if remote is configured):**

```bash
git remote add origin <url>   # only if user provided a remote
git push -u origin main
```

If no remote URL was given by the user, stop after `git commit` and inform them.

---

## Quality Gates

Before declaring the project done, verify every item:

- [ ] SPEC.md exists and is complete
- [ ] All public API in SPEC.md is implemented
- [ ] All edge cases in SPEC.md have a test
- [ ] `pytest` exits with 0 failures
- [ ] `black --check src/ tests/` exits cleanly
- [ ] `ruff check src/ tests/` exits cleanly
- [ ] `flake8 src/ tests/` exits cleanly
- [ ] `__version__ == "0.1.0.1"` in `__init__.py`
- [ ] README.md present with install + usage example
- [ ] `.gitignore` present
- [ ] `git log` shows at least one commit

---

## Common Pitfalls

**Don't skip SPEC.md.** The temptation to jump to code is always wrong. The spec forces
clarity about edge cases before they become bugs.

**Don't write tests after the fact as a formality.** Tests should falsify your
implementation. Write at least one test you expect might fail.

**Don't ignore linter warnings.** Fix the root cause, not the symptom.

**Don't use `# noqa` as a first resort.** It's a last resort with a comment explaining
why.

**Black and flake8 can conflict** on line length — use `--extend-ignore=E203,W503` and
set `max-line-length=88` in flake8 to match black's output.

**`src/` layout requires `pip install -e .`** to be importable. Remind the user if they
get `ModuleNotFoundError`.
