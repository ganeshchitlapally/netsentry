# NetSentry

[![CI](https://github.com/ganeshchitlapally/netsentry/actions/workflows/ci.yml/badge.svg)](https://github.com/ganeshchitlapally/netsentry/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Network flow anomaly detection plus an LLM triage agent, benchmarked honestly against
simple and supervised baselines on the UNSW-NB15 dataset.

> **Status: work in progress (Phase 1 of 5: data and features).** No model results yet. Every number
> that appears in this README will be produced by a script in this repo, saved under
> [`results/`](results/), and inserted into this file by `make readme`, never typed by hand.

## What this project will show

1. **Detection:** unsupervised detectors (Isolation Forest, autoencoder trained on benign
   traffic only) compared against a static-threshold rule and a supervised XGBoost upper bound.
   Metrics: PR-AUC, ROC-AUC, precision/recall/F1 at a validation-chosen threshold, false
   positives per 10,000 benign flows, and per-attack-category recall.
2. **Serving:** a FastAPI scoring service with measured p50/p95/p99 latency and throughput.
3. **Triage:** an LLM agent that turns an alert into a validated, structured triage report,
   evaluated against ground-truth attack categories and a non-LLM classifier baseline.

## Quickstart

Requires Linux, macOS or WSL2, plus [uv](https://docs.astral.sh/uv/) and `make`.

```bash
git clone https://github.com/ganeshchitlapally/netsentry.git
cd netsentry
make setup   # creates .venv from uv.lock (exact pins) and installs git hooks
make test    # no dataset or API keys required
```

Get the data. The official host blocks scripted downloads, so `make data` prints the exact
manual steps if files are missing, then verifies SHA-256 checksums:

```bash
make data FROM=/path/to/your/downloads   # imports, verifies, writes results/dataset_stats.json
```

`make help` lists all targets. Targets for later phases exit with a clear
"not implemented yet" message until those phases land.

## Dataset and its caveats

[UNSW-NB15](https://research.unsw.edu.au/projects/unsw-nb15-dataset), official train/test
CSVs, with a validation set carved from training data (never tuned on test). Read these
before trusting any number in this repo. Details and evidence are in
[docs/dataset.md](docs/dataset.md):

- **Synthetic lab traffic.** It was generated in a testbed, so results compare methods on
  this benchmark; they don't predict performance on an enterprise network.
- **Attacks are the majority class**, the reverse of real traffic. This makes precision look
  better than it would in deployment, so false positives per 10k benign flows are reported too.
- **Leaky columns.** `id` (row order) nearly predicts the label and is dropped. The TTL
  features are a testbed artifact, so every model is reported with and without them.
- **Duplicates.** Many rows are exact duplicates, and part of the test set appears verbatim in
  training. The validation split is duplicate-aware, and test metrics are also reported on
  test rows unseen in training.

## Results

<!-- RESULTS:START -->
_No results yet._
<!-- RESULTS:END -->

## Repository layout

```
src/netsentry/   data/ features/ models/ eval/ serving/ agent/
scripts/         entry points (download, train, evaluate, benchmark, agent eval, README render)
configs/         YAML configs (seeds, hyperparameters, provider settings)
results/         committed metrics (JSON/CSV) and plots; the only source for README numbers
docs/            decisions.md (design decisions), dataset notes
tests/           unit and integration tests (mock LLM provider, synthetic fixtures)
```

## Design decisions

See [docs/decisions.md](docs/decisions.md).

## License

[MIT](LICENSE) © Ganesh Chitlapally
