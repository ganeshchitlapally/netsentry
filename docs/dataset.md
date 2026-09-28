# UNSW-NB15: source, integrity and caveats

All figures referenced here live in [`results/dataset_stats.json`](../results/dataset_stats.json)
and [`results/leakage_audit.csv`](../results/leakage_audit.csv), written by `make data`
(`scripts/data_report.py`). This page explains them; it does not restate them by hand.

## Source and integrity

- Official page: <https://research.unsw.edu.au/projects/unsw-nb15-dataset> (Moustafa & Slay, 2015).
- Files used: the official partitioned CSVs `UNSW_NB15_training-set.csv` and
  `UNSW_NB15_testing-set.csv` (folder `CSV Files/Training and Testing Sets`), plus the
  optional feature description file `NUSW-NB15_features.csv`.
- The official host (a UNSW SharePoint folder) returns HTTP 403 to scripts, so the files are
  downloaded in a browser and imported with `make data FROM=<download dir>`.
- UNSW publishes no checksums. The SHA-256 hashes in `src/netsentry/data/download.py` were
  **pinned from the official files on 2026-09-28**; they prove you have the same bytes this
  repo was built on, not that those bytes are "official". Community mirrors were not used
  because their provenance cannot be verified.

## Split policy

- The official train/test split is kept as-is. The test set is used only for final
  evaluation; no threshold, hyperparameter or feature decision is made on it.
- A validation set is carved from the official training set: stratified by `attack_cat` and
  **group-aware on exact duplicate feature vectors** (see decision 004).

## Caveats a reader should know

1. **Synthetic lab traffic.** Traffic was generated with the IXIA PerfectStorm tool in a
   testbed: a mix of synthetic "normal" traffic and scripted attacks. Results here say
   how methods compare on this benchmark, not how they would perform on an enterprise
   network, where normal traffic is messier and attack mixes differ.
2. **Attacks are the majority class.** In both official splits most rows are attacks, the
   reverse of a real network. This matters for unsupervised detection, which assumes
   anomalies are rare, and it inflates precision-type metrics relative to a real
   deployment. That is why false positives per 10,000 benign flows is reported.
3. **Severe class imbalance among attack categories.** Some categories (e.g. Worms,
   Shellcode) have very few rows, so per-category recall for them is noisy.
4. **Many exact duplicates.** A large share of rows in each split repeat an earlier row's
   model inputs exactly, and part of the official test set also appears verbatim in the
   official training set. Final evaluation will report metrics on the full test set (for
   comparability with the literature) and on the test rows never seen in training.
5. **Label noise.** Some identical feature vectors appear with both labels, and more with
   different attack categories. No model can get all of these right.
6. **Leaky columns.**
   - `id` is a row counter, but the official files are ordered so that `id` alone
     separates attacks from normal traffic very well (it has the highest single-feature
     AUC in the audit). It is always dropped.
   - The TTL features (`sttl`, `dttl`, `ct_state_ttl`) reflect how the testbed hosts were
     configured: one threshold rule on `sttl` gets high training accuracy. They are
     kept in the default feature set for comparability, and every model is also
     evaluated without them (`no_ttl` feature set).
7. **Unseen categories in test.** Some `state` values occur only in the test split; the
   encoder handles unknown categories instead of failing.
