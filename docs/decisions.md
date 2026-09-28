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

---

## 004: Group-aware, stratified validation split

**What.** The validation set (20%) is carved from the official training set using
`StratifiedGroupKFold`: stratified on `attack_cat`, with rows grouped by a hash of their
model inputs so exact duplicates always land on the same side.

**Why.** The training CSV contains a large number of exact duplicate feature vectors
(`results/dataset_stats.json` → `duplicates`). A plain random split puts copies of the same
flow in both train and validation, so validation turns partly into a memorisation test, and
the thresholds chosen on it would be tuned on optimistic scores. The report confirms zero
duplicate groups shared between train and validation.

**Alternatives.** Random stratified split (leaks duplicates). Dropping duplicates entirely
(changes the class distribution and discards how often real traffic repeats). A time-based
split (the partitioned CSVs have no timestamps).

---

## 005: Leakage audit: drop `id`, ablate TTL features

**What.** `id`, `label` and `attack_cat` are never model inputs. The TTL features (`sttl`,
`dttl`, `ct_state_ttl`) are kept in the default `all` feature set, and every model is also
trained and evaluated on a `no_ttl` feature set.

**Why.** The audit (`results/leakage_audit.csv`) measures single-feature ROC-AUC against the
label on the training portion. `id` has the highest AUC of any column, because the official
files are ordered by class: a model given `id` would learn row order. The TTL features follow
the testbed's host configuration rather than attack behaviour. Their AUC is below the
0.9 flag threshold only because the relationship is non-monotonic, yet one `sttl` threshold
rule still gets high training accuracy (`best_single_sttl_threshold_rule_on_train`). Dropping
them silently would make results hard to compare with published work; keeping them silently
would overstate real-world performance. Reporting both answers "how much of the score comes
from the artifact?"

**Alternatives.** Drop the TTL features outright (hides the effect from readers); keep them
without comment (the most common choice in the literature, and misleading).

---

## 006: Preprocessing: signed log1p + standardisation, pooled one-hot categories

**What.** Numeric features: `sign(x)·log1p(|x|)` then `StandardScaler`. Categoricals (`proto`,
`service`, `state`): one-hot, with categories seen fewer than 20 times in training pooled into
one "infrequent" column. Categories unseen in training map to that column (or all zeros) at
inference time. The whole `ColumnTransformer` is fit on the training portion only.

**Why.** Byte, packet and load features span many orders of magnitude; without the log, the
autoencoder's reconstruction loss and the scaler are dominated by a few huge flows. `proto`
has over a hundred mostly-rare values; pooling keeps the input width manageable and avoids
columns fit on a handful of rows. Test data contains `state` values never seen in training,
so the encoder must not raise on unknown categories. Tree models don't need scaling, but one
shared pipeline keeps the serving path identical for every model.

**Alternatives.** `QuantileTransformer` (more robust to outliers, but it hides magnitude, which
matters for volume-based attacks); target/ordinal encoding for `proto` (target encoding needs
careful out-of-fold fitting to avoid leakage; ordinal imposes a fake order).

---

## 007: Manual download with pinned checksums instead of a mirror

**What.** `scripts/download_data.py` verifies files in `data/raw/` (or imports them from a
folder with `--from`) against SHA-256 hashes pinned from the official files. When files are
missing, it prints exact manual download steps and exits non-zero.

**Why.** The official SharePoint host returns HTTP 403 to scripted requests. Several community
mirrors exist, but none has verifiable provenance, and a silently modified copy would
corrupt every downstream number. Pinning the hashes means anyone who downloads by hand can
prove they have the same bytes this repo used.

**Alternatives.** A Kaggle or Hugging Face mirror (automatable, but provenance can't be
verified and it needs third-party credentials); scraping SharePoint (brittle, and against the
host's evident intent).
