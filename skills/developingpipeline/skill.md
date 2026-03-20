---
name: dev-pipeline
description: >
  Full Python feature development pipeline: implement a feature from a prompt, update tests,
  update README, run black + ruff (auto-fix warnings), then git commit and push.
  Use this skill whenever the user says "develop X", "implement feature Y", "add Z to the project",
  "write the code for ...", or asks to take a prompt and turn it into shipped, clean, committed code.
  Also trigger when the user says "run the pipeline", "do the full cycle", "commit and push after implementing",
  or any variant of feature-to-push workflow. Even partial requests like "implement and test X" or
  "implement, lint, commit" should use this skill.
---
 
# Dev Pipeline Skill
 
Implement a feature from a `$prompt`, harden it with tests, document it, enforce style, and ship it — all in one repeatable cycle.
 
---
 
## Phase 0 — Orientation (always run first)
 
```bash
# Confirm we're in a git repo with a clean-enough working tree
git status --short
git log --oneline -3
```
 
Identify:
- **Entry point / main module** (where the feature probably lives)
- **Test file(s)** (pytest convention: `tests/test_*.py` or `*_test.py`)
- **README path** (`README.md`, `README.rst`, or `docs/`)
- **pyproject.toml / setup.cfg** (for black/ruff config)
 
If any are missing, note it and create sensible defaults (see Phase 4).
 
---
 
## Phase 1 — Implement `$prompt`
 
1. **Parse the prompt** — extract: what to build, inputs/outputs, constraints, edge cases.
2. **Locate insertion point** — existing module or new file.
3. **Write the implementation** — follow existing code style; add type hints; no dead code.
4. **Self-review checklist before moving on:**
   - [ ] No `TODO` / `FIXME` left behind
   - [ ] No unused imports
   - [ ] Docstring on every public function/class
   - [ ] Edge cases handled (empty input, zero, None, overflow as relevant)
 
```python
# Pattern: always include a __all__ if the module is a public API
__all__ = ["new_function"]
 
def new_function(arg: Type) -> ReturnType:
    """One-line summary.
 
    Args:
        arg: Description.
 
    Returns:
        Description.
 
    Raises:
        ValueError: When arg is invalid.
    """
    ...
```
 
---
 
## Phase 2 — Update Tests
 
**Rule:** tests describe *behaviour*, not implementation. One test file per module.
 
### 2.1 Locate or create the test file
 
```bash
# Find existing test file
find . -name "test_*.py" -o -name "*_test.py" | head -20
```
 
If none exists:
```bash
mkdir -p tests
touch tests/__init__.py
touch tests/test_<module>.py
```
 
### 2.2 Write / extend tests
 
Cover at minimum:
| Category | What to test |
|---|---|
| Happy path | Normal inputs produce correct output |
| Edge cases | Empty, zero, single element, boundary values |
| Error paths | Invalid inputs raise the right exception |
| Regression | Any bug that prompted the feature |
 
```python
import pytest
from mypackage.module import new_function
 
class TestNewFunction:
    def test_basic(self):
        assert new_function(valid_input) == expected
 
    def test_empty_input(self):
        with pytest.raises(ValueError, match="empty"):
            new_function([])
 
    @pytest.mark.parametrize("inp,expected", [
        (1, 1),
        (2, 4),
        (10, 100),
    ])
    def test_parametrized(self, inp, expected):
        assert new_function(inp) == expected
```
 
### 2.3 Run tests — must be green before proceeding
 
```bash
python -m pytest tests/ -v --tb=short 2>&1 | tail -30
```
 
**If tests fail:** fix the implementation or the tests (whichever is wrong) before continuing. Do not proceed with red tests.
 
---
 
## Phase 3 — Update README
 
Find the README:
```bash
ls README* docs/index* 2>/dev/null | head -5
```
 
Add/update:
1. **One-liner** describing the new feature in the existing intro or feature list.
2. **Usage example** (minimal, copy-pasteable).
3. **API section** (if the project exposes a public API) — document the new function/class.
 
Keep it concise. Match the existing tone and formatting exactly.
 
```markdown
## New Feature Name
 
Short description of what it does and why.
 
```python
from mypackage import new_function
result = new_function(42)
```
```
 
---
 
## Phase 4 — Black Check
 
```bash
# Check first (no mutation yet — see what would change)
python -m black --check --diff . 2>&1 | head -40
 
# Apply formatting
python -m black .
 
# Confirm clean
python -m black --check . && echo "BLACK OK"
```
 
If `black` is not installed:
```bash
pip install black --quiet
```
 
---
 
## Phase 5 — Ruff Check + Fix
 
```bash
# Check
python -m ruff check . 2>&1 | head -60
 
# Auto-fix everything fixable
python -m ruff check --fix .
 
# Re-check — only unfixable warnings should remain
python -m ruff check . 2>&1 | head -40
```
 
### Handling unfixable warnings
 
| Code | Meaning | Action |
|---|---|---|
| `E501` | Line too long | Refactor the line manually |
| `ANN*` | Missing type annotation | Add annotation |
| `D*` | Docstring style | Fix docstring |
| `N*` | Naming | Rename (careful — may break API) |
| `S*` | Security | Evaluate; fix or `# noqa: Sxxx` with comment |
| `ERA001` | Commented-out code | Delete it |
 
**Goal:** zero warnings. If a warning is intentionally suppressed, add `# noqa: CODE  # reason`.
 
If `ruff` is not installed:
```bash
pip install ruff --quiet
```
 
---
 
## Phase 6 — Final Test Run
 
After formatting changes, re-run the full test suite once more to catch any accidental breakage:
 
```bash
python -m pytest tests/ -v --tb=short 2>&1 | tail -20
```
 
Must be green. If not, fix and re-run Phases 4–5.
 
---
 
## Phase 7 — Git Commit
 
### 7.1 Stage
 
```bash
git add -A
git status --short   # review what's staged
```
 
Unstage anything that shouldn't go in this commit (generated files, secrets, `.env`, etc.):
```bash
git reset HEAD <file>
```
 
### 7.2 Commit message
 
Follow Conventional Commits format:
 
```
<type>(<scope>): <short imperative summary>
 
<optional body: what and why, not how>
 
<optional footer: BREAKING CHANGE, fixes #issue>
```
 
Types: `feat` | `fix` | `refactor` | `test` | `docs` | `chore` | `perf`
 
Examples:
```
feat(parser): add support for base-4 encoded sequences
fix(totient): handle n=1 edge case in phi product formula
docs(README): document new XOR sum pipeline usage
```
 
```bash
git commit -m "feat(<scope>): <summary derived from $prompt>"
```
 
### 7.3 Verify commit
 
```bash
git log --oneline -5
git show --stat HEAD
```
 
---
 
## Phase 8 — Git Push
 
```bash
# Identify remote and branch
git remote -v
git branch --show-current
 
# Push
git push origin $(git branch --show-current)
```
 
**If push is rejected** (non-fast-forward):
```bash
git pull --rebase origin $(git branch --show-current)
# Resolve any conflicts, then:
git push origin $(git branch --show-current)
```
 
**If upstream is not set:**
```bash
git push --set-upstream origin $(git branch --show-current)
```
 
---
 
## Summary Checklist
 
Run through this before declaring done:
 
- [ ] Phase 1: Implementation written, self-reviewed
- [ ] Phase 2: Tests written/updated, all green
- [ ] Phase 3: README updated with usage example
- [ ] Phase 4: `black --check .` exits 0
- [ ] Phase 5: `ruff check .` exits 0 (or all suppressions documented)
- [ ] Phase 6: Tests still green after formatting
- [ ] Phase 7: Commit staged cleanly, message follows Conventional Commits
- [ ] Phase 8: Push succeeded, remote is up to date
 
---
 
## Error Recovery
 
| Situation | Fix |
|---|---|
| Tests fail after black | black changed string quotes inside assertions — recheck logic |
| ruff introduces import order issues | run `ruff check --fix` again; ruff's isort pass may need two rounds |
| Push rejected after rebase | check for conflicts in `git status`, resolve, `git rebase --continue` |
| black and ruff disagree on line length | set `line-length` consistently in `pyproject.toml` for both tools |
| No `pyproject.toml` | create minimal one (see below) |
 
### Minimal `pyproject.toml`
 
```toml
[tool.black]
line-length = 88
 
[tool.ruff]
line-length = 88
 
[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "D", "UP"]
ignore = ["D203", "D213"]   # prefer D211 + D212
 
[tool.pytest.ini_options]
testpaths = ["tests"]
```
