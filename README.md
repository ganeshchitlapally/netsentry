# NetSentry

[![CI](https://github.com/ganeshchitlapally/netsentry/actions/workflows/ci.yml/badge.svg)](https://github.com/ganeshchitlapally/netsentry/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Network flow anomaly detection plus an LLM triage agent, benchmarked honestly against
simple and supervised baselines on the UNSW-NB15 dataset.

> **Status: work in progress (Phase 0 of 5: scaffold).** No results yet. Every number
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

`make help` lists all targets. Targets for later phases exit with a clear
"not implemented yet" message until those phases land.

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
