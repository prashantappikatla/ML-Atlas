# Datasets

This directory stores raw and processed datasets for ML Atlas labs and experiments.

## Structure

```
datasets/
├── raw/          # Downloaded source data (gitignored for large files)
└── processed/    # Cleaned, feature-engineered data (gitignored for large files)
```

## Built-in Datasets (via scikit-learn)

The lab shared utilities (`labs/_shared/dataset_loader.py`) load these sklearn datasets automatically — no downloads needed:

| Name | Task | Samples | Features | Classes |
|---|---|---|---|---|
| `iris` | Classification | 150 | 4 | 3 |
| `digits` | Classification | 1797 | 64 | 10 |
| `wine` | Classification | 178 | 13 | 3 |
| `breast_cancer` | Classification | 569 | 30 | 2 |
| `diabetes` | Regression | 442 | 10 | — |

## Adding External Datasets

Place raw files in `datasets/raw/` and processed versions in `datasets/processed/`.
Large files (>10MB) are gitignored. Document each dataset in this file.

| Dataset | Source | Task | Size | Notes |
|---|---|---|---|---|
| — | — | — | — | — |
