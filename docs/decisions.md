# Design decisions

Short records of non-obvious choices: what was decided, why, and what else was considered.
Newest entries go at the bottom.

---

## 001: uv with a committed lockfile for dependency pinning

**What.** `pyproject.toml` declares direct dependencies with lower bounds; `uv.lock` pins
every package (including transitive ones) to an exact version and hash. `make setup`, CI and
Docker all install with `uv sync --locked`, which fails if the lock is out of date.

**Why.** Reproducibility from a fresh clone is a hard requirement. Hand-pinning `==` versions
in `pyproject.toml` pins only direct dependencies and lets transitive ones drift. A lockfile
with hashes pins the whole tree, and uv resolves and installs quickly enough for CI.

**Alternatives.** pip + `requirements.txt` from `pip-compile` (works, but slower and more
moving parts); Poetry (similar guarantees, heavier tool); conda (useful for CUDA, but
unnecessary here and harder to lock across platforms).

---

## 002: Linux-first tooling (Makefile + WSL2), `src/` layout

**What.** The Makefile and docs target Linux/macOS; Windows users run inside WSL2. Code lives
under `src/netsentry/` and is installed into the venv, and tests import the installed package.

**Why.** CI and the Docker image are Linux, so developing on Linux means the benchmark
numbers and the tooling are the same everywhere. The `src/` layout stops tests from
accidentally importing the working directory instead of the installed package.

**Alternatives.** A cross-platform task runner (`just`, `nox`, `invoke`) would support native
Windows, but `make` is universal on Linux and is what the project brief specifies.

---

## 003: Ruff pre-commit hook runs from the project venv

**What.** The pre-commit ruff hooks are `repo: local` hooks that call `uv run ruff`, instead of
the `ruff-pre-commit` mirror.

**Why.** The ruff version then comes from `uv.lock`, the same version CI uses. With the mirror,
its `rev:` and the locked ruff version can drift apart and disagree about formatting.

**Alternatives.** The `astral-sh/ruff-pre-commit` mirror, with its `rev` kept in sync by hand
or by a bot.
